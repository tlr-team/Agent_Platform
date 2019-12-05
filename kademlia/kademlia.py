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
        )
        self.add_contacts(sender)
        return True

    def exposed_store_value(self, sender: Contact, key: int, value: str):
        pass

    def exposed_find_value(self, from_contact: Contact, key: int):
        pass

    def exposed_find_node(self, from_contact: Contact, key: int):
        pass

    # endregion

    def add_contacts(self, contact: Contact):
        self.logger.debug(f'add_contacts :: Updating contact {contact}).')
