from .contact import Contact
from .bucketlist import BucketList
from .storage import StorageManager  # TODO: implement the SorageManager
from threading import Thread, Semaphore, Lock
from engine.utils.logger import getLogger
from rpyc import Service
from .utils import rpyc_connect, FakeNTP
from ..engine.utils.network import retry
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


class KademliaProtocol(Service):
    def __init__(self, storage: StorageManager, b=DefaultBSize, k=DefaultKSize):
        super(KademliaProtocol, self).__init__()
        self.k, self.b = k, b
        self.storage_manager = storage  # TODO: use it
        self.lock = Lock()
        self.service_port = 9000
        self.db = {}
        self.db_lock = Lock()
        self.logger = getLogger(name='KademliaProtocol')
        self.initialized = False
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
            return False
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

    # endregion
    def connect_to(self, contact):
        self.logger.debug(f'connect_to :: trying Contact:{contact}')
        connection = rpyc_connect(contact.ip, contact.port, timeout=1)
        connection.ping()
        self.logger.debug(f'connect_to :: Added Contact:{contact}')
        return connection

    def add_contacts(self, contact: Contact):
        self.logger.debug(f'add_contacts :: Updating contact {contact}).')
