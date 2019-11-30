from .contact import Contact
from .bucketlist import BucketList
from .dht import Id
from .storage import StorageManager  # TODO: implement the SorageManager
from threading import Thread, Semaphore, Lock
from socket import (
    socket,
    SOCK_DGRAM,
    SOL_SOCKET,
    SO_REUSEADDR,
    SOCK_STREAM,
    SO_BROADCAST,
)
from utils.network import Decode_Response, Encode_Request, Udp_Message
from hashlib import sha1


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
        self.service_port = 9000
        self.db = {}

    def _serve(self):
        with socket(type=SOCK_DGRAM) as serve_socket:
            serve_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            serve_socket.bind("", self.service_port)
            serve_socket.listen(10)
            while True:
                msg, addr = serve_socket.recvfrom(1024)
                Thread(target=self._attend, args=(msg, addr), daemon=True).start()

    def _attend(self, msg, addr):
        message = Decode_Response(msg)

        if 'ping' in message:
            pass
            # Thread(target = self.ping, args=(msg), daemon = True).start()
        elif 'pong' in message:
            Thread(target=self.ping, args=(msg, addr[0], addr[1]), daemon=True).start()
        elif 'store' in message:
            pass
        elif 'find_node' in message:
            pass
        elif 'find_node_ret' in message:
            pass
        elif 'find_value' in message:
            pass
        elif 'find_value_ret' in message:
            pass

    @property
    def contact(self):
        return self.__contact

    @property
    def bucket_list(self):
        return self.__bucket_list

    def ping(self, ip, port):
        Udp_Message({"ping": {}}, ip, port)

    def pong(self, ip, port):
        Udp_Message({"pong": {}}, ip, port)

    def store(self, key: Id, val: str):
        pass
        # Udp_Message({"store": {"id": Id, "value": val}}, ip, port)

    def find_node(self, sender: Contact, key: Id):
        raise NotImplementedError()
        # return contacts, val

    def find_value(self, sender: Contact, key: Id):
        raise NotImplementedError()
        # return contacts, val

    def handle_ping(self, msg):
        with self.lock:
            sender_contact = Contact.from_dict(
                {**msg['sender'], 'our_id': self.contact.id}
            )
            self.bucket_list.add_contact(sender_contact)
            Udp_Message({'pong': {}}, *sender_contact.addr)
        # return ourContact

    def handle_store(self, msg):  # sender: Contact, key: Id, val: str):
        with self.lock:
            sender_contact = Contact.from_dict(
                {**msg['sender'], 'our_id': self.contact.id}
            )
            self.bucket_list.add_contact(sender_contact)
            Udp_Message({'store_ret': {}}, *sender_contact.addr)

    def handle_find_node(self, msg):  # sender: Contact, key: Id):
        with self.lock:
            sender_contact = Contact.from_dict(
                {**msg['sender'], 'our_id': self.contact.id}
            )
            self.bucket_list.add_contact(sender_contact)
            # TODO
        # raise NotImplementedError()
        # return contacts, val

    def hanlde_find_value(self, msg):  # sender: Contact, key: Id):
        with self.lock:
            sender_contact = Contact.from_dict(
                {**msg['sender'], 'our_id': self.contact.id}
            )
            self.bucket_list.add_contact(sender_contact)
            # TODO
        # raise NotImplementedError()
        # return contacts, val
