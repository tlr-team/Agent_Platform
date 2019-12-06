from .contact import Contact
from .bucketlist import BucketList
from .storage import StorageManager  # TODO: implement the SorageManager
from threading import Thread, Lock
from engine.utils.logger import getLogger
from rpyc import Service,discover
from rpyc.utils.factory import DiscoveryError 
from .utils import rpyc_connect, KSortedQueue, ThreadRunner
from engine.utils.network import retry
from queue import Queue, Empty
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
DefaultAlfaSize = 3


class KademliaProtocol(Service):
    def __init__(
        self,
        storage=StorageManager(),
        b=DefaultBSize,
        k=DefaultKSize,
        a=DefaultAlfaSize,
    ):
        super(KademliaProtocol, self).__init__()
        self.k, self.b, self.a = k, b, a
        self.storage_manager = storage  # TODO: use it
        self.lock = Lock()
        self.service_port = 9000
        self.db = {}
        self.db_lock = Lock()
        self.logger = getLogger(name='KademliaProtocol')
        self.initialized = False
        self.started = False
        self.bucket_list: BucketList
        self.contact: Contact

    # region RemoteCall functions
    def exposed_init(self, contact):
        if self.initialized:
            return True
        self.contact = (
            contact if isinstance(contact, Contact) else Contact.from_json(contact)
        )
        self.bucket_list = BucketList(self.contact.id, k=self.k, b=self.b)
        self.logger.debug(f'exposed_init :: Node Initialized (id:{self.contact.id}).')
        self.initialized = True
        self.logger.debug(
            f'exposed_init :: Node Initialized(id:{self.contact.id},k:{self.k},b:{self.b}'
        )
        return True

    def exposed_ping(self, sender: Contact):
        if not self.initialized:
            self.logger.error(f'exposed_ping :: Node not initialized.')
            return False
        sender = Contact.from_json(sender)
        self.logger.info(f'exposed_ping :: <Ping> from {sender}.')
        self.update_contacts(sender)
        self.logger.debug(f'exposed_ping :: contact:{sender} stored.')
        return self.contact.to_json()

    def exposed_store(self, sender: Contact, key: int, value: str, store_time):
        self.logger.debug(
            f'exposed_store :: Storing ({key},{value}) at time {store_time}.'
        )
        if not self.initialized:
            self.logger.error(f'exposed_store :: Node not initialized.')
            return False
        self.logger.debug(f'exposed_store :: Requested by {sender}.')
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
        # self.logger.debug(f'exposed_store :: Finish with {sender}.')
        return True

    def exposed_find_value(self, sender: Contact, key: int):
        if not self.initialized:
            self.logger.error(f'exposed_find_value :: Node not initialized.')
            return None
        sender = Contact.from_json(sender)
        self.update_contacts(sender)
        self.logger.debug(f'exposed_find_value :: Requested by {sender}.')
        try:
            self.db_lock.acquire()
            value, store_time = self.db[key]
            self.logger.debug(f'exposed_find_value :: Found key:{key}, value:{value}.')
            self.db_lock.release()
            return value, store_time
        except KeyError:
            self.db_lock.release()
            self.logger.debug(f'exposed_find_value :: Key({key}) not found.')
            return None, 0

    def exposed_find_node(self, sender: Contact, key: int):
        if not self.initialized:
            self.logger.error(f'exposed_find_node :: Node not initialized.')
            return None
        sender = Contact.from_json(sender)
        self.update_contacts(sender)
        self.logger.debug(f'exposed_find_node :: Requested by {sender}.')
        result = []
        with self.bucket_list.buckets_lock:
            for c in self.bucket_list.get_closest(key):
                result.append(c.to_json())
                if len(result) >= self.k:
                    break
        self.logger.debug(
            f'exposed_find_node :: Sended {len(result)} contacts to {sender}.'
        )
        return result

    def exposed_iter_find_node(self, key: int):
        if not self.initialized:
            self.logger.error(f'exposed_iter_find_node :: Node not initialized.')
            return False
        if key == self.contact.id:
            self.logger.debug(
                f'exposed_iter_find_node :: The node.id({self.contact.id}) == key({key}).'
            )
            return self.contact.to_json()
        self.logger.debug(f'exposed_iter_find_node :: Strating iterative find node.')
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
                self.logger.debug(
                    f'exposed_iter_find_node :: Alpha:{queue.qsize()} contacts to look for.'
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
            self.logger.debug('find_value_lookup :: Getting a contact from the queue.')
            contact = queue.get(timeout=1)
        except Empty:
            self.logger.debug('find_value_lookup :: Empty queue.')
            return
        self.logger.debug(f'find_value_lookup :: do_find_node to contact:{contact}.')
        success, contacts = self.do_find_node(contact, key)
        if not success:
            self.logger.debug(f'find_value_lookup :: Unable to connect to {contact}.')
            return
        self.logger.debug(
            f'find_value_lookup :: do_find_value key({key}) to {contact}.'
        )
        success, value_time = self.do_find_value(contact, key)
        if not success:
            self.logger.debug(f'find_value_lookup :: Unable to connect to {contact}.')
            return
        self.update_contacts(contact)

        if value_time:
            value, time = value_time
            with value_lock:
                most_recent_value[0], most_recent_value[1] = (
                    value,
                    time if time > most_recent_value[1] else most_recent_value,
                )
                self.logger.debug(
                    f'find_value_lookup :: Update value key({key}) to {most_recent_value}.'
                )
        self.logger.debug(f'find_value_lookup :: Search key({key}) in contacts.')
        for contact_finded in contacts:
            if not self.do_ping(contact_finded)[0]:
                self.logger.debug(f'find_value_lookup :: Unable to connect to {contact_finded}.')
                continue
            self.update_contacts(contact_finded)
            queue_lock.acquire()
            if not contact_finded in visited:
                self.logger.debug(
                    f'find_value_lookup :: Adding {contact_finded} to pendings.'
                )
                visited.add(contact_finded)
                kclosest.add(contact_finded)
                queue.put(contact_finded)
            queue_lock.release()
    def connect_to(self, contact):
        self.logger.debug(f'connect_to :: trying Contact:{contact}')
        connection = rpyc_connect(contact.ip, contact.port, timeout=1)
        connection.ping()
        self.logger.debug(f'connect_to :: Added Contact:{contact}')
        return connection

    # region Do functions
    @retry(1, 1, message='do_ping(retry) :: Fail to connect')
    def do_ping(self, reciever: Contact):
        self.logger.debug(f'do_ping :: Node not initialized.')
        con = self.connect_to(reciever)
        result = con.root.ping(self.contact.to_json())
        return result

    @retry(1, 1, message='do_store(retry) :: Fail to connect')
    def do_store_value(self, reciever: Contact, key, value, store_time):
        self.logger.debug(f'do_store :: Storing ({key},{value}) in {reciever}.')
        con = self.connect_to(reciever)
        result = con.root.store(
            self.contact.to_json(), int(key), str(value), store_time
        )
        return result

    @retry(1, 1, message='do_find_node(retry) :: Fail to connect')
    def do_find_node(self, reciever: Contact, key):
        self.logger.debug(
            f'do_find_node :: Searching a node with key:{key} in {reciever}.'
        )
        con = self.connect_to(reciever)
        result = con.root.find_node(self.contact.to_json(), int(key))
        return result

    @retry(1, 1, message='do_find_value(retry) :: Fail to connect')
    def do_find_value(self, reciever: Contact, key):
        self.logger.debug(
            f'do_find_value :: Searching a value with key:{key} in {reciever}.'
        )
        con = self.connect_to(reciever)
        result = con.root.find_value(self.contact.to_json(), int(key))
        return result

    def update_contacts(self, contact: Contact):
        self.logger.debug(f'update_contacts :: Updating contact {contact}).')
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
                self.logger.debug(f'update_contacts :: To remove contact:{to_rem}.')
                bucket.remove_contact(to_rem)
                bucket.add_contact(contact)
            bucket.lock.release()
        self.logger.debug(f'update_contacts :: Done.')
        return
