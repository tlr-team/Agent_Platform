'''
Leader Db File
'''

from ..utils.leader_election import Leader_Election, StoppableThread
from threading import Lock
from ..utils.logger import getLogger
from time import sleep
from ..utils.network import Tcp_Message

class LDatabase:
    def __init__(self):
        self.dblock = Lock()
        self.database = {}
        self.main_count = 0
        self.node_count = 0
        self.is_full = True

    def insert(self, ip, id = None):
        with self.dblock:
            self.node_count += 1
            if not id:
                for key in self.database:
                    for i in range(0,2):
                        if self.database[key][i] == None:
                            self.database[key][i] = ip
                            return (key, i)
                self.database[self.main_count] = (ip,None)
                self.main_count += 1
                return (self.main_count -1 , 0)
            else:
                for i in range(0,2):
                    if self.database[id][i] == None:
                        self.database[id][i] = ip
                        return (key, i)

    def delete(self, ip):
        with self.dblock:
            self.node_count -= 1
            for key in self.database:
                for i in range(0,2):
                    if self.database[key][i] == ip:
                        self.database[key][i] = None
                        if self.database[key] == (None,None):
                            del self.database[key]
                            if key == self.main_count -1 :
                                self.main_count -= 1
                        return (key, i)

    def get_backup(self):
        with self.dblock:
            for key in self.database:
                if self.database[key][1] != None:
                    return (key, self.database[key][1])
            return None

    def __getitem__(self, value):
        return self.database[value]



class DbLeader(Leader_Election):
    def __init__(self, ip, mask, port, leport):
        self.ip = ip
        self.port = port
        self.le = Leader_Election(ip, mask, leport)
        self.database = {}
        self.freelist = []
        self.deadlist = []
        self.main_count = 0
        self.node_count = 0
        self.dblock = Lock()
        self.freelock = Lock()
        self.deadlock = Lock()
        self.logger = getLogger()

    def _start(self):
        self.le._start()

    def _check(self, time):
        while(True):
            if not self.le.im_leader:
                break
            lista = self.le.discover.Get_Partners()
            self._check_newones(lista)
            self._check_deadones(lista)            
            sleep(time)


    def _check_newones(self, lista):
        for i in lista:
            present = False
            for j in range(0,len(self.database.keys() - 1)):
                if present:
                    break
                for k in range(0,2):
                    if i == self.database[j][k]:
                        present = True
                        break
            if not present:
                if not i in self.database[-1]:
                    with self.freelock:
                        self.freelist.append(i)
                self.node_count += 1

    def _check_deadones(self, lista):
        for i in range(0,len(self.database.keys() - 1)):
            for j in range(0,2):
                if self.database[i][j] and self.database[i][j] not in lista:
                    with self.deadlock:
                        self.deadlist.append(self.database[i][j])



    #region database
    def _leinsert(self, ip, id = None):
        with self.dblock:
            self.node_count += 1
            if not id:
                for key in self.database:
                    for i in range(0,2):
                        if self.database[key][i] == None:
                            self.database[key][i] = ip
                            return (key, i)
                self.database[self.main_count] = (ip,None)
                self.main_count += 1
                return (self.main_count -1 , 0)
            else:
                for i in range(0,2):
                    if self.database[id][i] == None:
                        self.database[id][i] = ip
                        return (key, i)

    def _ledelete(self, ip):
        with self.dblock:
            self.node_count -= 1
            for key in self.database:
                for i in range(0,2):
                    if self.database[key][i] == ip:
                        self.database[key][i] = None
                        if self.database[key] == (None,None):
                            del self.database[key]
                            if key == self.main_count -1 :
                                self.main_count -= 1
                        return (key, i)

    def _leget_backup(self):
        with self.dblock:
            for key in self.database:
                if self.database[key][1] != None:
                    return (key, self.database[key][1])
            return None
    #endregion