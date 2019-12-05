'''
Shared Db File
'''

from .simple_database import SimpleDataBase
from socket import socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread
from ..utils.network import Tcp_Sock_Reader, Encode_Request, Tcp_Message
from time import sleep
from ..utils.logger import getLogger

class SharedDataBase(SimpleDataBase):
    def __init__(self, ip, dbport, leaderelectionport):
        super(SharedDataBase,self).__init__()
        self.logger = getLogger()
        self.ip = ip
        self.dbport = dbport
        self.backup = ""
        Thread(target=self._client_Serve, daemon=True).start()
        while(True):
            sleep(10)
            
        
    def _client_Serve(self):
        with socket(type=SOCK_STREAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            sock.bind((self.ip,self.dbport))
            sock.listen(10)
            
            self.logger.info(f'Database Service Initiated at {self.ip}, {self.dbport}')

            while(True):
                client, addr = sock.accept()
                Thread(target=self._process_request,args=(client,addr),daemon=True).start()
    
    def _process_request(self, sock, addr):
        request = Tcp_Sock_Reader(sock)

        self.logger.info(f'Recieved {request} from {addr}')

        if 'get' in request:
            if request['get'] == 'list':
                sock.send(Encode_Request(self.dbs.keys()))

                self.logger.info(f'Full Service List Sent to {addr}')

            else:
                message = self._get(request['get'])
                sock.send(Encode_Request(message))

                self.logger.info(f'Sent {message} to {addr}')
        elif 'post' in request:
            if(self.backup != ''):
                
                self.logger.info(f'Backup Update Sent to {self.backup}')

                Tcp_Message(request, self.backup, self.dbport)
            self._insert(request['post'],{ 'ip':request['ip'],'port':request['port'],'url':request['url']})

