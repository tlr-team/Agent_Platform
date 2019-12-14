'''
Leader Election Shared Db File
'''

from .leader import DbLeader
from .sdb import SharedDataBase
from time import sleep
from ..utils.network import Tcp_Message, Void, Tcp_Sock_Reader, ServerTcp, Encode_Request
from ..utils.logger import getLogger
from hashlib import sha1
from threading import Thread
from multiprocessing import Lock, Process, Value


class LESDB(DbLeader, SharedDataBase):
    def __init__(self, ip, mask, dbport, leport, world_port, logger=getLogger(), pt=10, rt=20, ttl=4, check_time=5, assing_job_time=10, remove_dead_time=10):
        SharedDataBase.__init__(self, ip, mask, dbport, logger)
        DbLeader.__init__(self, ip, mask , leport, logger, pt , rt , ttl )
        self.world_port = world_port
        self.logger = logger
        self.check_time = check_time
        self.assing_job_time = assing_job_time
        self.remove_dead_time = remove_dead_time

    def _assign_work(self, time):
        while(True):
            if not self.im_leader:
                break
            if len(self.freelist):
                with self.freelock:
                    while(len(self.freelist)):
                        ip = self.freelist.pop()
                        if ip != self.ip and not self._exist(ip):
                            info = Tcp_Message({'INFO':''},ip,self.dbport)
                            if info != None:
                                self.logger.debug(f'recieved info {info} from {ip}')
                                val, backup = self._is_useful_info(info, ip)
                                if not val:
                                    id, backup = self._leinsert(ip)
                                    self.logger.debug(f'id and backup to {ip}: {id, backup}')
                                    Tcp_Message({'ID':id}, ip, self.dbport, Void)
                                    self.logger.debug(f" database {self.database}")
                                if backup:
                                    with self.dblock:
                                        set_backup = self.database[id][0]
                                    Tcp_Message({'SET_BACKUP':ip},set_backup,self.dbport, Void)
                                    self.logger.debug(f'Sended SET_BACKUP to {set_backup}')
                                    Tcp_Message({'TO_BACKUP':set_backup},ip,self.dbport, Void)
                                    self.logger.debug(f'Sended TO_BACKUP to {ip}')
                                self.logger.debug(f" database {self.database}")
            #else:
                #self.logger.debug(f'NO IP FOUND FOR JOB')
            sleep(time)
    
    def _is_useful_info(self, info, ip):
        ID = info['INFO_ACK']
        if ID >= 0:
            with self.dblock:
                for i in [0,1]:
                    if ID == self.main_count or not self.database[ID][i]:
                        self.database[ID] = self._build_tuple(ID, i, ip)
                        self.logger.debug(f'REUSED INFO { info } from {ip}')
                        return (True, i)
        return (False, 0)
        
    def _get_help(self, ID):
        self.logger.debug(f'ID at get_help {ID}')
        if ID in self.database and self.database[ID][1] != None:
            newip = self.database[ID][1]
            self.dblogger.debug(f'{newip} found for job at {ID}')
            Tcp_Message({'SET_BACKUP':''}, newip, self.dbport, Void)
            self.logger.debug(f'Sended SET_BACKUP to {newip}')
            with self.dblock:
                a, b = self.database[ID]
                self.database[ID] = (b,a)
            self.dblogger.debug(f'database {self.database}')
        else:
            val = self._leget_backup()
            if val:
                self.logger.debug(f'BACKUP AVIABLE FOUND FOR RESCUE')
                Tcp_Message({'RESET':''}, val[1], self.dbport, Void)
                #self.logger.debug(f'SENDED RESET FLAG TO {val[1]}')
                self._ledelete(val[1])
                self.logger.debug(f'database {self.database} after _ledelte{val[1]}')    
            else:
                self.logger.debug(f'NO BACKUP AVIABLE FOR RESCUE')

    def _remove_dead(self, time):
        while(True):
            if not self.im_leader:
                break
            if len(self.deadlist):
                with self.deadlock:
                    while(len(self.deadlist)):
                        ip = self.deadlist.pop()
                        val = self._ledelete(ip)
                        if val:
                            index = val[1]
                            if index == 0:
                                self._get_help(index)
                            self.logger.debug(f'Deleted {ip}')
                        else:
                            self.logger.debug(f'{ip} not found for delete')
            sleep(time)

    def _world_serve(self):
        self.logger.info(f'World Server Initiated at {self.world_port}')
        ServerTcp(self.ip,self.world_port,self._world_attend,self.logger,lambda x: not x.im_leader,self)
    
    def _world_attend(self, sock, addr):
        message = Tcp_Sock_Reader(sock)
        self.logger.debug(f'Recieved {message} from {addr}')
        keyword = 'get' if 'get' in message else 'post' if 'post' in message else None
        if keyword:
            ip = self._resolve_ip(message,keyword)
            self.lelogger.debug(f'IP RESOLVED {ip}')
            if ip:
                response = Tcp_Message(message, ip, self.dbport, Tcp_Sock_Reader if keyword == 'get' else Void)
                self.logger.debug(f'RECIEVED {response} from {ip}')
                if response != None:
                    sock.send(Encode_Request(response))
                    self.logger.debug(f'Sended {response} TO {addr}')
            else:
                self.lelogger.debug(f"IP NOT resolved, {ip}")
        sock.close()

    def _resolve_db(self, msg):
        return None if not self.main_count else sha1(str(msg).encode()).digest()[-1] % self.main_count

    def _resolve_ip(self, msg, keyword):
        ID = self._resolve_db(msg[keyword])
        self.lelogger.debug(f'ID Found {ID}')
        return self.database[ID][0] if ID != None else None

    def serve(self,time):
        Thread(target=self._serve,daemon=True,name='Discover Server Daemon').start()
        Thread(target=self._check_leader,daemon = True, name='Leader Election Daemon').start()

        while(True):
            thread_list = []
            if self.im_leader:
                self.logger.debug('Im Leader Now')
                time = 10
                self.logger.debug(f'live or dead checker initiated')
                thread_list.append(Thread(target=self._check, args=(self.check_time,), name='Live or Dead Checker'))
                self.logger.debug(f'world server initiated')
                thread_list.append(Thread(target=self._world_serve, name='World Server Daemon'))
                self.logger.debug(f'job assigner initiated')
                thread_list.append(Thread(target=self._assign_work,args=(self.assing_job_time,),name='Job Assigner'))
                self.logger.debug(f'Dead Burrier')
                thread_list.append(Thread(target=self._remove_dead,args=(self.remove_dead_time,),name='Dead Burrier'))
            else: 
                self.logger.debug('Im Worker Now')
                #thread_list.append(Thread(target=ServerTcp,args=(self.ip,self.dbport,self._process_request, self.logger, lambda x: x.im_leader, self)))
                thread_list.append(Process(target=Worker_Process,args=(self.ip,self.dbport, self._process_request, validate, self.leader_dhared_memory, self.leaderprocesslock)))

            for i in thread_list:
                i.start()

            for i in thread_list:
                i.join()
            self.logger.debug(f'Changed Function')

def Worker_Process(ip, port, function, shared_memory_func, shared_memory, lock):
    logger = getLogger()
    logger.debug(f'Worker Server Initieted at {ip},{port}')
    Thread(target=ServerTcp,args=(ip, port, function, logger, shared_memory_func, shared_memory, lock),daemon=True, name='Server').start()
    while(True):
        if shared_memory_func(shared_memory, lock):
            logger.debug(f'Worker Job Ended')
            exit()
        #logger.warning(f'valor de la memoria compartida, {shared_memory.value}')
        sleep(1)

def validate(shared, lock = None):
    if lock:
        with lock:
            return shared.value
    else:
        return shared.value
