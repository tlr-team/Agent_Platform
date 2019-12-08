'''
Shared Db File
'''

from .simple_database import SimpleDataBase
from socket import socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from threading import Thread, Lock
from ..utils.network import Tcp_Sock_Reader, Encode_Request, Tcp_Message, ServerTcp
from time import sleep
from ..utils.logger import getLogger
from ..utils.leader_election import Leader_Election

class SharedDataBase(SimpleDataBase):
    def __init__(self, ip, mask, dbport):
        SimpleDataBase.__init__(self)
        self.logger = getLogger()
        self.ip = ip
        self.dbport = dbport
        self.backup = ""
        self.im_backup = False
        self.to_backup = ""
        self.id = -1

    def _process_request(self, sock, addr):
        if not self.im_backup or self.to_backup == addr[0]:
            request = Tcp_Sock_Reader(sock)

            self.logger.debug(f'Recieved {request} from {addr}')

            if 'get' in request:
                if request['get'] == 'list':
                    full_list = Encode_Request([ a for a in self.dbs])
                    sock.send(full_list)

                    self.logger.debug(f'Full Service List {full_list} Sent to {addr}')

                else:
                    message = self._get(request['get'])
                    sock.send(Encode_Request(message))

                    self.logger.debug(f'Sent {message} to {addr}')
            elif 'post' in request:
                if(self.backup != ''):
                    
                    self.logger.debug(f'Backup Update Sent to {self.backup}')

                    Tcp_Message(request, self.backup, self.dbport)
                self._insert(request['post'],{ 'ip':request['ip'],'port':request['port'],'url':request['url']})

            elif 'ID' in request:
                self.id = request['ID']

            elif 'INFO' in request:
                sock.send({"INFO_ACK":self.id})

            elif 'SET_BACKUP' in request:
                self.im_backup = False
                self.backup = request['SET_BACKUP']
                self.to_backup = ""

            elif 'TO_BACKUP' in request:
                self.im_backup = True
                self.to_backup = request['TO_BACKUP']
                self.backup = ""
        sock.close()

