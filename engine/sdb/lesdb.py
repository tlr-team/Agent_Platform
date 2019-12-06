'''
Leader Election Shared Db File
'''

from .leader import DbLeader
from .sdb import SharedDataBase
from time import sleep
from ..utils.network import Tcp_Message, Void, Tcp_Sock_Reader, ServerTcp

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
        pass

    def _world_attend(self, sock, addr):
        pass



