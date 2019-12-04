'''
Shared Db File
'''

from .simple_database import SimpleDataBase
from socket import socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread
from ..utils.network import Tcp_Sock_Reader, Encode_Request
from time import sleep

class SharedDataBase(SimpleDataBase):
    def __init__(self, ip, dbport, leaderelectionport, ):
        super(SharedDataBase,self).__init__()
        self.ip = ip
        self.dbport = dbport
        Thread(target=self._client_Serve, daemon=True).start()
        while(True):
            sleep(10)
            
        
    def _client_Serve(self):
        with socket(type=SOCK_STREAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            sock.bind(self.ip,self.dbport)
            sock.listen(10)

            while(True):
                client, addr = sock.accept()
                Thread(target=self._process_request,args=(client,addr),daemon=True).start()
    
    def _process_request(self, sock, addr):
        request = Tcp_Sock_Reader(sock)
        if 'get' in request:
            sock.send(Encode_Request(self._get(request['get'])))
        if 'post' in request:
            self._insert(request['post'],{ 'ip':request['ip'],'port':request['port'],'url':request['url']})

