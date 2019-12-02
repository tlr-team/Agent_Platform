from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from json import dumps, loads
from .network import Get_Subnet_Host_Number,Send_Broadcast_Message,Decode_Response,Encode_Request,Get_Broadcast_Ip,Discovering,Get_Subnet_Host_Number
from threading import Thread

class Leader_Election:
    def __init__(self, ip, mask, port):
        self.brd = Get_Broadcast_Ip(ip,mask)
        self.discover = Discovering(port,self.brd,,8)
        self.mask = mask
        self.ip = ip
        self.im_leader = False
        self.iwas_leader = False
        self.leader = None
        Thread(target=self._check_leader,daemon = True).start()

    def _check_leader(self, time = 10):
        while(True):
            ips = self.discover.partners.keys()
            self.leader = ips.sort(key=lambda x : Get_Subnet_Host_Number(x,self.mask))[-1] if len(self.discover.partners) else None
            if self.leader:
                if self.ip == self.leader:
                    self.im_leader = True
                    self.iwas_leader = True
                else:
                    self.im_leader = False
                    self.iwas_leader = False
            sleep(time)

    def Im_Leader(self):
        return self.im_leader

    def Leader(self):
        return self.leader