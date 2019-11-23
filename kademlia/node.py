from .contact import Contact
from .bucketlist import BucketList
from .dht import Id
from .storage import StorageManager  # TODO: implement the SorageManager


class Node:
    '''
    Encapsulate the funcionality of a Kademlia's Node.
    '''

    def __init__(
        self, contact: Contact, storage: StorageManager, cache_storage: StorageManager
    ):
        self.__contact = contact
        self.__bucket_list = BucketList(self.contact.id)
        self.storage_manager = storage
        self.cache_manager = cache_storage

    @property
    def contact(self):
        return self.__contact

    @property
    def bucket_list(self):
        return self.__bucket_list

    def ping(self, sender: Contact):
        raise NotImplementedError()
        # return ourContact

    def store(self, sender: Contact, key: Id, val: str):
        raise NotImplementedError()

    def find_node(self, sender: Contact, key: Id):
        raise NotImplementedError()
        # return contacts, val

    def find_value(self, sender: Contact, key: Id):
        raise NotImplementedError()
        # return contacts, val
