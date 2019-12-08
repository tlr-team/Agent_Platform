'''
Leader Election Shared Db File
'''

from .leader import DbLeader
from .sdb import SharedDataBase
from time import sleep
from ..utils.network import Tcp_Message, Void, Tcp_Sock_Reader, ServerTcp
from hashlib import sha1
from threading import Thread


class LESDB(DbLeader, SharedDataBase):
    def __init__(self, ip, mask, dbport, leport, world_port):
        SharedDataBase.__init__(self, ip, mask, dbport)
        DbLeader.__init__(self, ip, mask , leport)
        self.world_port = world_port

    def _assign_work(self, time):
        while(True):
            if not self.im_leader:
                break
            if len(self.freelist):
                with self.freelock:
                    while(len(self.freelist)):
                        ip = self.freelist.pop()
                        info = Tcp_Message({'INFO':''},ip,self.dbport)
                        id, backup = self._leinsert(ip)
                        Tcp_Message({'ID':id}, ip, self.dbport)
                        if backup:
                            with self.dblock:
                                set_backup = self.database[id][0]
                            Tcp_Message({'SET_BACKUP':ip},set_backup,self.dbport, Void)
                            Tcp_Message({'TO_BACKUP':set_backup},ip,self.dbport, Void)
            sleep(time)

    def _remove_dead(self, time):
        while(True):
            if not self.im_leader:
                break
            if len(self.freelist):
                with self.deadlock:
                    while(len(self.deadlist)):
                        ip = self.deadlist.pop()
                        self._ledelete(ip)
            sleep(time)

    def _world_serve(self):
        self.logger.info(f'World Server Initiated at {self.world_port}')
        ServerTcp(self.ip,self.world_port,self._world_attend,self.logger,lambda x: x.im_leader,self)

    def _world_attend(self, sock, addr):
        message = Tcp_Sock_Reader(sock)
        self.logger.debug(f'Recieved {message} from {addr}')
        keyword = 'get' if 'get' in message else 'post' if 'post' in message else None
        if keyword:
            ip = self._resolve_ip(message,keyword)
            if ip:
                response = Tcp_Message(message, ip, self.dbport, Tcp_Sock_Reader if keyword == 'get' else Void)
                if response:
                    sock.send(response)
        sock.close()

    def _resolve_db(self, msg):
        return sha1(str(msg).encode()).digest()[-1] % self.main_count

    def _resolve_ip(self, msg, keyword):
        ID = self._resolve_db(msg[keyword])
        return self.database[ID]

    def serve(self,time):
        Thread(target=self._check_leader,daemon = True, name='Leader Election Daemon').start()
        Thread(target=self._serve,daemon=True,name='Discover Server Daemon').start()

        while(True):
            thread_list = []
            if self.im_leader:
                self.logger.debug('Im Leader Now')
                thread_list.append(Thread(target=self._check, args=(10), name='Live or Dead Checker'))
            else: 
                self.logger.debug('Im Worker Now')
                thread_list.append(Thread(target=ServerTcp,args=(self.ip,self.dbport,self._process_request), daemon=True))

            for i in thread_list:
                i.join()
            self.logger.debg(f'Changed Function')
        pass



