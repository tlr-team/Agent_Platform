from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from json import dumps, loads
from .network import Get_Subnet_Host_Number,Send_Broadcast_Message,Decode_Response,Encode_Request,Get_Broadcast_Ip,Discovering,Get_Subnet_Host_Number
from threading import Thread, Event
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


class Leader_Election:
    def __init__(self, ip, mask, port):
        self.logger = getLogger()
        self.brd = Get_Broadcast_Ip(ip,mask)
        self.discover = Discovering(port,self.brd,self.logger,3,8)
        self.mask = mask
        self.ip = ip
        self.im_leader = False
        self.iwas_leader = False
        self.leader = None
        
    def _start(self):
        Thread(target=self._check_leader,daemon = True).start()
        self.discover._start()

    def _check_leader(self, time = 10):
        self.logger.info(f'Leader Election: Check Leader Deamon Initiated')
        while(True):
            ips = self.discover.Get_Partners()
            if len(self.discover.partners): 
                ips.sort(key=lambda x : Get_Subnet_Host_Number(x,self.mask))
                if self.leader != ips[-1]:
                    self.leader = ips[-1]
                    self.logger.info(f'New Leader {self.leader}')
            if self.leader:
                if self.ip == self.leader:
                    self.logger.debug(f'Im the Leader')
                    self.im_leader = True
                    self.iwas_leader = True
                else:
                    self.logger.debug(f'Leader: {self.leader}')
                    self.iwas_leader = self.im_leader
                    self.im_leader = False
            else:
                self.leader = None
            sleep(time)

    def Im_Leader(self):
        return self.im_leader

    def Leader(self):
        return self.leader