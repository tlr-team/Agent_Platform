from .contact import Contact
from .bucketlist import BucketList
from .storage import StorageManager  # TODO: implement the SorageManager
from threading import Thread, Semaphore, Lock
from rpyc import Service
from socket import (
    socket,
    SOCK_DGRAM,
    SOL_SOCKET,
    SO_REUSEADDR,
    SOCK_STREAM,
    SO_BROADCAST,
)


class Kademlia(Service):
    def __init__(self, contact: Contact, storage: StorageManager):
        super(Kademlia, self).__init__()
        self.contact = contact
        self.bucket_list = BucketList(self.contact.id)
        self.storage_manager = storage
        self.lock = Lock()
        self.service_port = 9000
        self.db = {}

