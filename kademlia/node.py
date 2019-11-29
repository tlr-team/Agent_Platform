from .contact import Contact
from .bucketlist import BucketList
from .dht import Id
from .storage import StorageManager  # TODO: implement the SorageManager
from threading import Thread, Semaphore
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from utils.network import Decode_Response, Encode_Request


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
        self.service_port = 9000

    def _serve(self):
        with socket(type = SOCK_DGRAM) as serve_socket:
            serve_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            serve_socket.bind("",self.service_port)
            service_port.listen(10)
            while(True):
                msg, addr = local.recvfrom(1024)
                message = Decode_Response(msg)

                if 'ping' in message:
                    pass
                elif 'pong' in message:
                    pass
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
                #Thread(target = self._attend, args=(msg,addr), daemon = True).start()

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
