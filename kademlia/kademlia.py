from .contact import Contact
from .bucketlist import BucketList
from .storage import StorageManager  # TODO: implement the SorageManager
from threading import Thread, Lock
from engine.utils.logger import setup_logger, debug, error, info
from rpyc import Service,discover,connect
from rpyc.utils.factory import DiscoveryError 
from .utils import rpyc_connect, KSortedQueue, ThreadRunner
from engine.utils.network import retry
from queue import Queue, Empty
from random import randint
from time import sleep
from json import dump
from socket import (
    socket,
    SOCK_DGRAM,
    SOL_SOCKET,
    SO_REUSEADDR,
    SOCK_STREAM,
    SO_BROADCAST,
)

DefaultKSize = 3  # FIXME: Put a correct value
DefaultBSize = 160
DefaultAlfaSize = 1

setup_logger(name='Kademlia', to_file=True)

class KademliaProtocol(Service):
    '''
    Encapsulate the funcionality of a Kademlia's Node protocol.
    '''
    def __init__(
        self,
        storage=StorageManager(),
        b=DefaultBSize,
        k=DefaultKSize,
        a=DefaultAlfaSize,
        t_expire = 8,
        t_rediscover= 10,
    ):
        super(KademliaProtocol, self).__init__()
        self.k, self.b, self.a = k, b, a
        self.db = {}
        self.db_lock = Lock()
        self.initialized = False
        self.started = False
        self.bucket_list: BucketList
        self.contact: Contact

        def threaded_expire():
            entries_to_remove = set()
            while True:
                if not self.db or not self.started:
                    sleep(t_expire)
                    continue
                debug(f'[Expiration] Collector begins')
                with self.db_lock:
                    debug(f'[Expiration]db-before:{self.db}\nto_remove:{entries_to_remove}')
                    for k,tup in list(self.db.items()):
                        if (k,tup) in entries_to_remove:
                            del self.db[k]
                    entries_to_remove = set((k,tup) for k,tup in self.db.items())
                    debug(f'[Expiration]db-after:{self.db}')
                debug(f'[Expiration] Sleep: {t_expire}')
                sleep(t_expire)

        def threaded_update_network():
            while True:
                if self.initialized:
                    debug(f'[Update Net] Start.')
                    self.exposed_update_network()
                debug(f'[Update Net] Sleep: {t_rediscover}')
                sleep(t_rediscover)
                
        Thread(target=threaded_update_network, daemon=True).start()
        Thread(target=threaded_expire, daemon=True).start()

    def exposed_update_network(self):
        if not self.initialized:
            error(f'Node not initialized')
        service_name = KademliaProtocol.service_name(self.__class__)
        nodes = discover(service_name)
        for node in nodes:
            tcontact = Contact(*node)
            debug(f'Pinging to node: {tcontact}')
            result, _ = self.do_ping(tcontact)
            debug(('Successfull' if result else 'Unsuccessfull') + f' ping to node: {tcontact}')

    @staticmethod
    def service_name(cls):
        return cls.__name__.split('Service')[0]

    # region RemoteCall functions
    def exposed_init(self, contact):
        if self.initialized:
            return True
        
        self.contact = (
            contact if isinstance(contact, Contact) else Contact.from_json(contact)
        )
        self.bucket_list = BucketList(self.contact.id, k=self.k, b=self.b)
        self.initialized = True
        debug(
            f'Node Initialized(id:{self.contact.id},ip:{self.contact.ip}),k:{self.k},b:{self.b}'
        )
        return True

    def exposed_join_to_network(self, contact: str):
        debug(f'Recieved {contact}, to creatme.')
        assert self.exposed_init(contact)
        contact = Contact.from_json(contact)
        while not self.started:
            try:
                if not self.initialized:
                    raise Exception(f'KademliaProtocol initializing has fail.')
                try:
                    debug(f'Searching for {KademliaProtocol.service_name(self.__class__)} RPyC Service.')
                    nodes = discover(KademliaProtocol.service_name(self.__class__))
                    debug(f'Finded: {nodes}.')
                except DiscoveryError as e:
                    error(f'Service:{KademliaProtocol.service_name(self.__class__)} not found - {e}.')
                    raise DiscoveryError(f'Service:{KademliaProtocol.service_name(self.__class__)} not found - {e}.')
                _any = 0
                for ip,port in nodes:
                    if ip == self.contact.ip and port == self.contact.port:
                        continue
                    count = 0
                    while count < 5:
                        try:
                            conn = connect(ip, port)
                            debug(f'Connection established with ({ip}:{port}), attemp: {count}.')
                            resp = conn.root.ping(self.contact.to_json())
                            debug(f'<PING> to ({ip}:{port}) response: ({resp})-{("Ping" if resp else "No ping")} responding.')
                            if resp:
                                contact = Contact.from_json(resp)
                                break
                            else:
                                error(f'Bad Response resul({resp}) from ({ip}:{port}).')
                                raise Exception(f'connection fail.')
                        except Exception as e:
                            error(f'Exception:\n{e}')
                            debug(f'Retrying to connect to ({ip}:{port})')
                            count += 1
                    if count == 5:
                        debug(f'Connection not established with ({ip}:{port})')
                        sleep(1)
                        continue
                    _any += 1
                    assert self.contact != contact
                    self.update_contacts(contact)
                if not _any:
                    raise Exception(f'No node discovered is connected.')
                try:
                    # At this point im connected at least with one node
                    self.exposed_iter_find_node(self.contact.id)
                except Exception as e:
                    raise Exception(f'Interrupted first exposed_iter_find_node because {e}.')
                for i in range(self.k):
                    if not self.bucket_list[i]:
                        continue
                    count = 0
                    while count < 5:
                        key = randint(2**i, 2**(i+1)-1)
                        try:
                            self.exposed_iter_find_node(key)
                            break
                        except Exception as e:
                            error(f'Interrupted exposed_iter_find_node because: {e}')
                    if count == 5:
                        debug(f'exposed_iter_find_node not allowed in bucket {i}')
                self.started = True
            except Exception as e:
                error(f'NODE NOT JOINNED {e}')
                debug(f'sleep a while for keep retrying')
                sleep(0.3)  
        return True
             
    def exposed_ping(self, sender: Contact):
        if not self.initialized:
            error(f'Node not initialized.')
            return False
        sender = Contact.from_json(sender)
        info(f'<Ping> from {sender}.')
        self.update_contacts(sender)
        debug(f'contact:{sender} stored.')
        return self.contact.to_json()

    def exposed_store(self, sender: Contact, key: int, value: str, store_time):
        # with self.db_lock:
        debug(
            f'Storing ({key},{value}) at time {store_time}.\ndb:{self.db}'
        )
        if not self.initialized:
            error(f'Node not initialized.')
            return False
        debug(f'Requested by {sender}.')
        if sender:
            sender = Contact.from_json(sender)
            self.update_contacts(sender)
        try:
            self.db_lock.acquire()
            stored_value, time = self.db[key]
        except KeyError:
            stored_value, time = (value, store_time)
        self.db[key] = (
            (value, store_time) if time < store_time else (stored_value, time)
        )
        debug(f'Stored at this node: ({key},{value}) at time {store_time}.')
        self.db_lock.release()
        self.export()
        debug(f'Finish with store requested by {sender}.')
        return True

    def exposed_find_value(self, sender: Contact, key: int):
        if not self.initialized:
            error(f'Node not initialized.')
            return None
        sender = Contact.from_json(sender)
        self.update_contacts(sender)
        debug(f'Requested by {sender}.')
        try:
            self.db_lock.acquire()
            value, store_time = self.db[key]
            debug(f'Found key:{key}, value:{value}.')
            self.db_lock.release()
            return value, store_time
        except KeyError:
            self.db_lock.release()
            debug(f'Key({key}) not found.')
            return None

    def exposed_find_node(self, sender: Contact, key: int):
        if not self.initialized:
            error(f'Node not initialized.')
            return None
        sender = Contact.from_json(sender)
        self.update_contacts(sender)
        debug(f'Requested by {sender}.')
        result = []
        for c in self.bucket_list.get_closest(key):
            result.append(c.to_json())
            if len(result) >= self.k:
                break
        debug(
            f'Sended {len(result)} contacts to {sender}.\n{result}'
        )
        return result

    def exposed_iter_find_node(self, key: int):
        if not self.initialized:
            error(f'Node not initialized.')
            return False
        if key == self.contact.id:
            debug(
                f'The node.id({self.contact.id}) == key({key}).'
            )
            return self.contact.to_json()
        debug(f'Strating iterative find node.')
        queue = Queue()
        visited = set()
        kclosest = KSortedQueue(self.k, self.contact.id)
        #
        queue.put(self.contact)
        visited.add(self.contact)
        kclosest.add(self.contact)
        for contact in self.bucket_list.get_closest(key):
            queue.put(contact)
            visited.add(contact)
            kclosest.add(contact)
            if queue.qsize() >= self.a:
                debug(
                    f'Alpha:{queue.qsize()} contacts to look for.'
                )
                break
        container = ThreadRunner(
            self.a,
            queue.qsize,
            target=self.find_node_lookup,
            args=(key, queue, kclosest, visited, Lock()),
        )
        container.start()
        for cont in kclosest:
            if cont.id == key:
                return cont.to_json()
        return None

    def exposed_iter_store(self, key, value, store_time):
        if not self.initialized:
            error(f'Node not initialized.')
            return False

        debug(f'Strating iterative store.')
        queue = Queue()
        visited = set()
        kclosest = KSortedQueue(self.k, self.contact.id)
        #
        queue.put(self.contact)
        visited.add(self.contact)
        kclosest.add(self.contact)
        for contact in self.bucket_list.get_closest(key):
            queue.put(contact)
            visited.add(contact)
            kclosest.add(contact)
            if queue.qsize() >= self.a:
                debug(
                    f'Alpha:{self.a} contacts to look for.'
                )
                break
        container = ThreadRunner(
            self.a,
            queue.qsize,
            target=self.store_lookup,
            args=(key, queue, kclosest, visited, Lock()),
        )
        container.start()
        success = 0

        for cont in kclosest:
            debug(
                f'do_store_value to {cont} of {key}:({value},{store_time}).'
            )
            if not self.do_store_value(cont, key, value, store_time)[0]:
                error(f'Unable to connect to (kclosest) iteration {cont}.')
            else:
                success += 1
        return success != 0

    def exposed_iter_find_value(self, key):
        if not self.initialized:
            error(f'Node not initialized.')
            return None

        debug(f'Strating iterative find value.')
        queue = Queue()
        visited = set()
        kclosest = KSortedQueue(self.k, self.contact.id)
        most_recent_value = [None, -1]
        #
        queue.put(self.contact)
        visited.add(self.contact)
        kclosest.add(self.contact)
        for contact in self.bucket_list.get_closest(key):
            queue.put(contact)
            visited.add(contact)
            kclosest.add(contact)
            if queue.qsize() >= self.a:
                debug(
                    f'Alpha:{queue.qsize()} contacts to look for.'
                )
                break

        container = ThreadRunner(
            self.a,
            queue.qsize,
            target=self.find_value_lookup,
            args=(key, queue, kclosest, visited, most_recent_value, Lock(), Lock()),
        )
        container.start()

        value, time = most_recent_value
        if value is None:
            return None
        debug(f'Storing {key}:({value},{time}) kclosest contacts .')
        for cont in kclosest:
            debug(
                f'Storing {key},({most_recent_value}) in Contact:{cont}.'
            )
            if not self.do_store_value(cont, key, value, time)[0]:
                debug(
                    f'Success stored in {contact}'
                )
        return value,time
    # endregion    
    def find_value_lookup(
        self,
        key: int,
        queue: Queue,
        kclosest,
        visited: set,
        most_recent_value,
        queue_lock,
        value_lock,
    ):
        contact = None
        try:
            debug('Getting a contact from the queue.')
            contact = queue.get(timeout=1)
        except Empty:
            debug('Empty queue.')
            return
        debug(f'do_find_node to contact:{contact}.')
        success, contacts = self.do_find_node(contact, key)
        if not success:
            debug(f'Unable to connect to {contact}.')
            return
        debug(
            f'do_find_value key({key}) to {contact}.'
        )
        success, value_time = self.do_find_value(contact, key)
        if not success:
            debug(f'Unable to connect to {contact}.')
            return
        self.update_contacts(contact)

        if value_time:
            value, time = value_time
            with value_lock:
                most_recent_value[0], most_recent_value[1] = (
                    value,
                    time if time > most_recent_value[1] else most_recent_value,
                )
                debug(
                    f'Update value key({key}) to {most_recent_value}.'
                )
        debug(f'Search key({key}) in contacts({contacts}).')
        for contact_finded in contacts:
            if not self.do_ping(contact_finded)[0]:
                debug(f'Unable to connect to {contact_finded}.')
                continue
            self.update_contacts(contact_finded)
            queue_lock.acquire()
            if not contact_finded in visited:
                debug(
                    f'Adding {contact_finded} to pendings.'
                )
                visited.add(contact_finded)
                kclosest.add(contact_finded)
                queue.put(contact_finded)
            queue_lock.release()


    def store_lookup(self, key: int, queue: Queue, kclosest, visited: set, lock: Lock):
        contact = None
        try:
            debug('Getting a contact from the queue.')
            contact = queue.get(timeout=1)
        except Empty:
            debug('Empty queue.')
            return
        debug(f'do_find_node to contact:{contact}.')
        success, contacts = self.do_find_node(contact.to_json(), key)
        if not success:
            debug(f'Unable to connect to (do_find_node fail) {contact}.')
            return
        debug(f'Connected to (do_find_node succes) {contact}.')
        self.update_contacts(contact)
        contacts = map(Contact.from_json, contacts)
        debug(f'Peers to search: {list(contacts)}.')
        for contact_finded in contacts:
            if contact_finded == self.contact:
                continue
            debug(f'Pinging to (contacts finded bucle) {contact_finded}.')
            if not self.do_ping(contact_finded)[0]:
                debug(
                    f'Unable to connect to (contacts finded bucle) {contact_finded}.'
                )
                continue
            self.update_contacts(contact_finded)
            lock.acquire()
            if not contact_finded in visited:
                debug(
                    f'Adding (contacts finded bucle) {contact_finded} to pendings.'
                )
                visited.add(contact_finded)
                queue.put(contact_finded)
                kclosest.add(contact_finded)
            lock.release()

    def find_node_lookup(self, key, queue: Queue, kclosest, visited: set, lock: Lock):
        contact = None
        try:
            debug('Getting a contact from the queue.')
            contact = queue.get(timeout=1)
        except Empty:
            debug('Empty queue.')
            return
        debug(f'do_find_node to contact:{contact}.')
        success, contacts = self.do_find_node(contact, key)
        if not success:
            debug(f'Unable to connect to {contact}.')
            return
        debug(f'Connected to {contact}.')
        self.update_contacts(contact)
        contacts = map(Contact.from_json, contacts)
        for contact_finded in contacts:
            if contact_finded == self.contact:
                continue
            if not self.do_ping(contact_finded)[0]:
                debug(
                    f'Unable to connect to {contact_finded}.'
                )
                continue
            self.update_contacts(contact_finded)
            lock.acquire()
            if not contact_finded in visited:
                debug(
                    f'Adding {contact_finded} to pendings.'
                )
                visited.add(contact_finded)
                queue.put(contact_finded)
                kclosest.add(contact_finded)
            lock.release()

    def connect_to(self, contact):
        debug(f'trying to connect to {contact}.')
        try:
            connection = connect(contact.ip, contact.port, config={'timeout':1})
            debug(f'Pinging (from rpyc_connection) to :{contact}')
            connection.ping()
        except Exception as e:
            error(e)
        debug(f'Connected to contact:{contact}')
        return connection

    def export(self):
        self.db_lock.acquire()
        with open(f'log/data.txt', 'w') as f:
            dump(self.db, f, indent=True)
        self.db_lock.release()

    # region Do functions
    @retry(1, 1, message='do_ping(retry) :: Fail to connect')
    def do_ping(self, to_reciever: Contact):
        result = None
        if to_reciever == self.contact:
            debug(f'Pinging to myself.')
            return self.exposed_ping(to_reciever) 

        debug(f'Node not initialized.')
        con = self.connect_to(to_reciever)
        debug(f'Trying to ping to contact:{to_reciever}')
        result = con.root.ping(self.contact.to_json())
        con.close()
        return result

    @retry(1, 1, message='do_store_value(retry) :: Fail to connect')
    def do_store_value(self, to_reciever: Contact, key, value, store_time):
        result = None
        if to_reciever == self.contact:
            debug(f'Storing in myself {key}:({value},{store_time}).')
            return self.exposed_store(self.contact.to_json(), int(key), str(value), store_time)
        try:
            con = self.connect_to(to_reciever)
        
            debug(f'Trying to store to contact:{to_reciever}')
            result = con.root.store(
                self.contact.to_json(), int(key), str(value), store_time
            )
        except Exception as e:
            error(f'Has stopped because {e}')
            con.close()
            return False
        con.close()
        debug(f'Successfully stored at contact: {to_reciever} result: {result}')
        return result

    @retry(1, 1, message='do_find_node(retry) :: Fail to connect')
    def do_find_node(self, to_reciever: Contact, key):
        result = None
        if to_reciever == self.contact:
            debug(f'Find_node in myself {key}.')
            return self.exposed_find_node(self.contact.to_json(), key)
        try:
            con = self.connect_to(to_reciever)
            debug(f'Trying to find node to contact:{to_reciever}')
            result = con.root.find_node(self.contact.to_json(), int(key))
        except Exception as e:
            error(f'Has stopped because {e}')
            con.close()
            return False
        con.close()
        debug(f'Successfully find node with contact: {to_reciever} result: {result}')
        return result

    @retry(1, 1, message='do_find_value(retry) :: Fail to connect')
    def do_find_value(self, to_reciever: Contact, key):
        result = None
        if to_reciever == self.contact:
            debug(f'Find_value in myself {key}.')
            return self.exposed_find_value(self.contact.to_json(), key)
        try:
            con = self.connect_to(to_reciever)
            debug(f'Trying to find value to contact:{to_reciever}')
            result = con.root.find_value(self.contact.to_json(), int(key))
        except Exception as e:
            error(f'Has stopped because {e}')
            con.close()
            return False
        con.close()
        return result
    # endregion

    def update_contacts(self, contact: Contact):
        debug(f'Updating contact {contact}).')
        if contact == self.contact:
            return
        if not self.bucket_list.add_contact(contact):
            # bucket full
            to_rem = None
            bucket = self.bucket_list.get_bucket(contact.id)
            bucket.lock.acquire()
            for cont in bucket:
                if not self.do_ping(cont):
                    to_rem = cont
                    break
            if to_rem:
                debug(f'To remove contact:{to_rem}.')
                bucket.remove_contact(to_rem)
                bucket.add_contact(contact)
            bucket.lock.release()
        debug(f'Done.')
        return

