'''
Leader Db File
'''

from ..utils.leader_election import Leader_Election, StoppableThread
from ..utils.logger import getLogger
from threading import Lock
from ..utils.logger import getLogger
from time import sleep
from ..utils.network import Tcp_Message
from threading import Thread

class DbLeader(Leader_Election):
    def __init__(self, ip, mask, leport, logger = getLogger(), pt=10, rt=20, ttl=4):
        Leader_Election.__init__(self,ip,mask,leport, logger, pt, rt, ttl)
        self.database = {}
        self.freelist = []
        self.deadlist = []
        self.main_count = 0
        self.node_count = 0
        self.dblock = Lock()
        self.freelock = Lock()
        self.deadlock = Lock()
        self.dbleaderlogger = logger

    def _dbleader_start(self, time):
        Thread(target=self._check, args=(time), daemon=True, name="Leader Checker")
        self._start()     

    def _check(self, time):
        while(True):
            if not self.im_leader:
                break
            lista = self.Get_Partners()
            self.lelogger.debug(f'Partners {lista}')
            self._check_newones(lista)
            #self.lelogger.debug(f' deadones checker initated')
            self._check_deadones(lista)            
            sleep(time)


    def _check_newones(self, lista):
        for i in lista:
            present = False
            for key in self.database:
                if present:
                    break
                for k in range(0,2): 
                    if i == self.database[key][k]:
                        #self.lelogger.debug(f'IP already in database {i}')
                        present = True
                        break                    
            if not present:
                if not i in self.freelist and i != self.ip:
                    self.dbleaderlogger.debug(f' IP FOUND {i}')
                    with self.freelock:
                        self.freelist.append(i)
                self.node_count += 1

    def _check_deadones(self, lista):
        for _,val in self.database.items():
            for j in range(0,2):
                with self.deadlock:
                    if val[j] and val[j] not in lista and val[j] not in self.deadlist:
                        self.dbleaderlogger.debug(f'IP LOST {val[j]}')
                        self.deadlist.append(val[j])



    #region database
    def _leinsert(self, ip, id = None):
        if ip != self.ip:
            with self.dblock:
                self.node_count += 1
                if not id:
                    for i in [0,1]:
                        for key in self.database:
                            if self.database[key][i] == None:
                                self.database[key] = self._build_tuple(key, i, ip)
                                return (key, i)
                    self.database[self.main_count] = (ip,None)
                    self.main_count += 1
                    return (self.main_count -1 , 0)
                else:
                    for i in range(0,2):
                        if self.database[id][i] == None:
                            self.database[id] = self._build_tuple(id, i, ip)
                            return (key, i)

    def _ledelete(self, ip):
        with self.dblock:
            self.node_count -= 1
            for key in self.database:
                for i in range(0,2):
                    if self.database[key][i] == ip:
                        self.database[key] = self._build_tuple(key,i, None)
                        if self.database[key] == (None,None):
                            del self.database[key]
                            if key == self.main_count -1 :
                                self.main_count -= 1
                        return (key, i)
            return None

    def _leget_backup(self):
        with self.dblock:
            for key in self.database:
                if self.database[key][1] != None:
                    return (key, self.database[key][1])
            return None

    def _build_tuple(self, key, i, val):
        with self.dblock:
            if key in self.database:
                other = self.database[key][(i-1)%2]
                tup = (other, val) if i else (val,other)
            else:
                tup = (val, None)
            return tup

    def _exist(self, ip):
        with self.dblock:
            for _,tup in self.database.items():
                if ip in tup:
                    return True
            return False
    #endregion
