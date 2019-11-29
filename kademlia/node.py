from .contact import Contact
from .bucketlist import BucketList
from .dht import Id
from .storage import StorageManager  # TODO: implement the SorageManager
from utils.network import Decode_Response, Encode_Request, Udp_Message
from threading import Lock
import socket as sock


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
        self.lock = Lock()

    @property
    def contact(self):
        return self.__contact

    @property
    def bucket_list(self):
        return self.__bucket_list

    # def loop(self):
    #     while True:
    #         rawmsg, addr = self.listener.recv(2048)
    #         msg = Decode_Response(rawmsg)
    # if msg.get('ping', None) != None:
    #     self.ping(msg['ping'])
    # elif msg.get('store', None) != None:
    #     self.store(msg['store'])
    # elif msg.get('find_node',None) != None:
    #     self.find_node(msg['find_node'])
    # elif msg.get('find_value')

    def ping(self, msg):
        with self.lock:
            sender_contact = Contact.from_dict(msg['sender'])
            self.bucket_list.add_contact(sender_contact)
            Udp_Message(self.contact.to_dict, *sender_contact['addr'])
        # return ourContact

    def store(self, msg):  # sender: Contact, key: Id, val: str):
        with self.lock:
            pass

    def find_node(self, msg):  # sender: Contact, key: Id):
        with self.lock:
            sender_contact = Contact.from_dict(msg['sender'])
            self.bucket_list.add_contact(sender_contact)
            # TODO
        # raise NotImplementedError()
        # return contacts, val

    def find_value(self, sender: Contact, key: Id):
        with self.lock:
            sender_contact = Contact.from_dict(msg['sender'])
            self.bucket_list.add_contact(sender_contact)
            # TODO
        # raise NotImplementedError()
        # return contacts, val
