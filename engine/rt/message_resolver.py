from socket import (
    socket,
    SOCK_DGRAM,
    SOL_SOCKET,
    SO_REUSEADDR,
    SOCK_STREAM,
    SO_BROADCAST,
)
from time import sleep
from json import loads, dumps
from threading import Thread, Semaphore
from queue import Queue
from ..utils.network import (
    Decode_Response,
    Encode_Request,
    Send_Broadcast_Message,
    Tcp_Sock_Reader,
    Tcp_Message,
    Udp_Message,
    Udp_Response,
    WhoCanServeMe,
    Get_Broadcast_Ip
)
from io import BytesIO
from random import randint

# Funcionamiento del Router:
# Hilo1 busca un listado de mq (similar al cliente) y pide un request y lo encola en una lista si esta esta vacia (ojo, semaforo)
# Hilo2 desencola el request si existe , lo procesa y se conecta finalmente con el cliente con el resultado final

class Message_Resolver:
    def __init__(self ,ip ,mask, brd_port=10001, thread_count = 1, db_port=10002):
        # mutex
        self.servers = []
        self.mutex = Semaphore()
        self.Broadcast_Address = Get_Broadcast_Ip(ip,mask)
        self.Broadcast_Port = brd_port
        self.sm_ip = None
        self.bd_port = db_port
        self.thread_count = thread_count

    def start(self):
        searcher = Thread(target=self._searcher,daemon=True,name="recieve")
        Thread(target=self._discover_server, daemon=True).start()
        for i in range(0, self.thread_count):
            Thread(target=self._worker,daemon=True,name="worker" + str(i)).start()
        searcher.start()
        searcher.join()
    
    def _searcher(self):
        print('Searcher initiated')
        WhoCanServeMe(self.Broadcast_Address, self.Broadcast_Port, self.servers, self.mutex, 10)

    def _discover_server(self):
        print('Discover Initiated')
        with socket(type=SOCK_DGRAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            sock.bind(('', 10003))
            while(True):
                msg, addr = sock.recvfrom(1024)
                post = Decode_Response(msg)
                print(post, addr)
                if 'ME' in post:
                    if post['ME'] == 'MQ':
                        with self.mutex:
                            if not addr[0] in self.servers:
                                print(f'SERVERS UPDATED WITH {addr[0]}')
                                self.servers.append(addr[0])
                    elif post['ME'] == 'DF':
                        self.sm_ip = addr[0]

    def _worker(self):
        print('Worker Intiated')
        while(True):
            with self.mutex:
                #TODO LEO AQUIIIIIIIIIII
                if len(self.servers) and self.sm_ip:
                    choice = self.servers[randint(0, len(self.servers) - 1)]
                    req = Udp_Message({'get':''}, choice, self.Broadcast_Port , Udp_Response, 3)
                    print(f'Recieved {req} from {choice}')
                    if req:
                        if "get" in req:
                            ip = req["ip"]
                            port = req["port"]
                            info = req["get"]
                            msg = {"get":info}
                            response = None
                            if info == "full_list":
                                #TODO FULL LIST
                                #response = Tcp_Message(msg,self.am_ip,self.bd_port)
                                print('FULL LIST SENDED')
                            else:
                                response = Tcp_Message(msg,self.sm_ip,self.bd_port)
                            #Enviar la respuesta
                            Udp_Message(response,ip,port)
                            print(response, f'SENDED TO {ip},{port}')
                            
                        # Pedido desde un productor
                        elif 'post' in req:

                            #Mandar el update a la bd1
                            #Mandar el update a la bd2
                            #TODO MANDAR EL POST AL AMS
                            Tcp_Message(req,self.sm_ip,self.bd_port)
                            print('UPDATE SENDED')
            sleep(2)