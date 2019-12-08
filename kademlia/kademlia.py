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

setup_logger(name='Kademlia')

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
    ):
        super(KademliaProtocol, self).__init__()
        self.k, self.b, self.a = k, b, a
        self.lock = Lock()
        self.db = {}
        self.db_lock = Lock()
        self.initialized = False
        self.started = False
        self.bucket_list: BucketList
        self.contact: Contact
    
    @property
    def service_name(self):
        return self.__class__.__name__.split('Service')[0]

    # region RemoteCall functions
    def exposed_init(self, contact):
        if self.initialized:
            return True
        self.contact = (
            contact if isinstance(contact, Contact) else Contact.from_json(contact)
        )
        self.bucket_list = BucketList(self.contact.id, k=self.k, b=self.b)
        debug(f'Node Initialized (id:{self.contact.id}).')
        self.initialized = True
        debug(
            f'Node Initialized(id:{self.contact.id},k:{self.k},b:{self.b}'
        )
        return True

    def exposed_join_to_network(self, contact: str):
        self.exposed_init(contact)
        contact = Contact.from_json(contact)
        while not self.started:
            try:
                if not self.initialized:
                    raise Exception(f'KademliaProtocol initializing has fail.')
                try:
                    debug(f'Searching for {self.service_name} RPyC Service.')
                    nodes = discover(self.service_name)
                    debug(f'Finded: {nodes}.')
                except DiscoveryError as e:
                    raise DiscoveryError(f'Service:{self.service_name} not found - {e}.')
                _any = 0
                for ip,port in nodes:
                    if ip == self.contact.ip and port == self.contact.port:
                        continue
                    count = 0
                    while count < 5:
                        try:
                            conn = connect(ip, port)
                            debug(f'Connection established with ({ip}:{port})')
                            resp = conn.root.ping(self.contact.to_json())
                            debug(f'<PING> to ({ip}:{port}) response: {resp}.')
                            if resp:
                                contact = Contact.from_json(resp)
                                debug(f'Connection established with ({ip}:{port}).')
                                break
                            else:
                                raise Exception(f'connection not initialized.')
                        except Exception as e:
                            error(f'Retrying to connect to ({ip}:{port}), Exception:\n{e}')
                            count += 1
                    if count == 5:
                        debug(f'Connection not established with ({ip}:{port})')
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
                buck_len = len(self.bucket_list)
                for i in range(buck_len):
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
        return False
             
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
        debug(
            f'Storing ({key},{value}) at time {store_time}.'
        )
        if not self.initialized:
            error(f'Node not initialized.')
            return False
        debug(f'Requested by {sender}.')
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
        self.db_lock.release()
        # debug(f'Finish with {sender}.')
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
        with self.bucket_list.buckets_lock:
            for c in self.bucket_list.get_closest(key):
                result.append(c.to_json())
                if len(result) >= self.k:
                    break
        debug(
            f'Sended {len(result)} contacts to {sender}.'
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
                    f'Alpha:{queue.qsize()} contacts to look for.'
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
                error(f'Unable to connect to {cont}.')
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
        for cont in kclosest:
            debug(
                f'Storing {key},({most_recent_value}) in Contact:{cont}.'
            )
            if not self.do_store_value(cont, key, value, time)[0]:
                debug(
                    f'Success stored in {contact}'
                )
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
        debug(f'Search key({key}) in contacts.')
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
        success, contacts = self.do_find_node(contact, key)
        if not success:
            debug(f'Unable to connect to {contact}.')
            return
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
        connection = connect(contact.ip, contact.port, {'timeout':1})
        connection.ping()
        debug(f'Added Contact:{contact}')
        return connection

    # region Do functions
    @retry(1, 1, message='do_ping(retry) :: Fail to connect')
    def do_ping(self, to_reciever: Contact):
        if to_reciever == self.contact:
            return None
        debug(f'Node not initialized.')
        con = self.connect_to(to_reciever)
        result = con.root.ping(self.contact.to_json())
        return result

    @retry(1, 1, message='do_store(retry) :: Fail to connect')
    def do_store_value(self, to_reciever: Contact, key, value, store_time):
        if to_reciever == self.contact:
            return None

        con = self.connect_to(to_reciever)
        result = con.root.store(
            self.contact.to_json(), int(key), str(value), store_time
        )
        return result

    @retry(1, 1, message='do_find_node(retry) :: Fail to connect')
    def do_find_node(self, to_reciever: Contact, key):
        if to_reciever == self.contact:
            return None

        con = self.connect_to(to_reciever)
        result = con.root.find_node(self.contact.to_json(), int(key))
        return result

    @retry(1, 1, message='do_find_value(retry) :: Fail to connect')
    def do_find_value(self, to_reciever: Contact, key):
        if to_reciever == self.contact:
            return None

        con = self.connect_to(to_reciever)
        result = con.root.find_value(self.contact.to_json(), int(key))
        return result
    # endregion

    def update_contacts(self, contact: Contact):
        debug(f'Updating contact {contact}).')
        if contact == self.contact:
            return
        if not self.bucket_list.add_contact(contact):
            # bucket full
            with self.bucket_list.buckets_lock:
                bucket = self.bucket_list._get_bucket(contact.id)
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

