from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from json import dumps, loads
from .network import Get_Subnet_Host_Number,Send_Broadcast_Message,Decode_Response,Encode_Request,Get_Broadcast_Ip,Get_Subnet_Host_Number,ServerUdp
from threading import Thread, Event, Semaphore
from multiprocessing import Process, Lock, Value
from .logger import getLogger

class StoppableThread(Thread):
    '''
    Clase que permite detener una hebra
    '''

    def __init__(self,*args,**kwargs):
        super(StoppableThread, self).__init__(*args,**kwargs)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        self._stop_event.is_set()

def Void(time):
    pass

class Discovering:
    def __init__(self, port, broadcast_addr, logger, publish_time=10, refresh_time=20 ,ttl = 4):
        self.partners = {}
        self.port = port
        self.b_addr = broadcast_addr
        self.mutex = Semaphore()
        self.publish_time = publish_time
        self.refresh_time = refresh_time
        self.ttl = ttl
        self.disclogger = logger

    def Get_Partners(self):
        with self.mutex:
            return [a for a in self.partners.keys()]
    
    def _serve(self):
        Thread(target=self._write, daemon=True).start()
        Thread(target=self._refresh, daemon=True).start()
        self.disclogger.info(f'Discover Server Initiated at {self.port}')
        ServerUdp('',self.port,self._listen, self.disclogger)

    # Hilo que va a recibir el mensaje de broadcast y procesarlo
    def _listen(self, msg ,ip):
        if ip[0] not in self.partners:
            self.disclogger.debug(f"NEW IP FOUND {ip[0]}")
            with self.mutex:
                self.partners[ip[0]] = self.ttl
                self.disclogger.debug(f'TTL restablished for {ip[0]}')

    # Hilo que va a enviar cada cierto tiempo definido un mensaje broadcast para decir que esta vivo
    def _write(self):
        self.disclogger.info(f'Discover write Daemon initiated')
        while True:
            Send_Broadcast_Message("Hello", self.b_addr, self.port)
            sleep(self.publish_time)

    #Hilo que va a refrescar el estado de la tabla
    def _refresh(self):
        self.disclogger.info(f'Discover refresh Daemon initiated')
        while(True):
            with self.mutex:
                temp = {}
                for name, val in self.partners.items():
                    if val > 1:
                        temp[name] = val - 1
                    else:
                        self.disclogger.debug(f'TTL EXPIRED {name}')
                self.partners = temp
                #self.disclogger.debug(f'partnerts :{temp}')
            sleep(self.refresh_time)

class Leader_Election(Discovering):
    def __init__(self, ip, mask, port, logger = getLogger(), pt = 10, rt=20, ttl=4):
        Discovering.__init__(self, port, Get_Broadcast_Ip(ip,mask), logger,pt, rt, ttl)
        self.mask = mask
        self.ip = ip
        self.leader_dhared_memory = Value('i',0)
        self.leaderprocesslock = Lock()
        self.leaderthreadlock = Semaphore()
        self.iwas_leader = False
        self.leader = None
        self.lelogger = logger
        
    def _start(self):
        Thread(target=self._check_leader,daemon = True, name='Leader Election Daemon').start()
        Thread(target=self._serve,daemon=True,name='DiscoverServer').start()

    def _check_leader(self, time = 30):
        self.lelogger.info(f'Leader Election: Check Leader Daemon Initiated')
        while(True):
            ips = self.Get_Partners()
            if len(self.partners): 
                ips.sort(key=lambda x : Get_Subnet_Host_Number(x,self.mask))
                if self.leader != ips[-1]:
                    self.leader = ips[-1]
                    self.lelogger.info(f'New Leader {self.leader}')
            if self.leader:
                if self.ip == self.leader:
                    self.lelogger.debug(f'Im the Leader')
                    self.im_leader = True
                    self.iwas_leader = True
                else:
                    self.lelogger.debug(f'Leader: {self.leader}')
                    self.iwas_leader = self.im_leader
                    self.im_leader = False
            else:
                self.leader = None
            sleep(time)

    @property
    def im_leader(self):
        with self.leaderthreadlock:
            with self.leaderprocesslock:
                return self.leader_dhared_memory.value

    @im_leader.setter
    def im_leader(self, val):
        with self.leaderthreadlock:
            with self.leaderprocesslock:
                self.leader_dhared_memory.value = int(val)

    

    def Leader(self):
        return self.leader