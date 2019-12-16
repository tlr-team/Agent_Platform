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
    def __init__(self ,ip ,mask, db_port, brd_port, thread_count = 1):
        # mutex
        self.servers = []
        self.mutex = Semaphore()
        self.Broadcast_Address = Get_Broadcast_Ip(ip,mask)
        self.Broadcast_Port = brd_port
        self.am_ip = "127.0.0.1"
        self.sm_ip = "192.168.2.7"
        self.bd_port = db_port
        self.thread_count = thread_count

    def serve(self):
        searcher = Thread(target=self._searcher,daemon=True,name="recieve")
        for i in range(0, self.thread_count):
            Thread(target=self._worker,daemon=True,name="worker" + str(i)).start()
        searcher.start()
        searcher.join()
    
    def _searcher(self):
        WhoCanServeMe(self.Broadcast_Address, self.Broadcast_Port, self.servers, self.mutex)

    def _worker(self):
        with self.mutex:
            if len(self.servers):
                with self.mutex:
                    choice = self.servers[randint(0, len(self.servers) - 1)]
                req = Udp_Message({'get':''}, choice, self.Broadcast_Port , Udp_Response)
                if "get" in req:
                    ip = req["ip"]
                    port = req["port"]
                    info = req["get"]
                    msg = {"get":info}
                    response = None
                    if info == "full_list":
                        response = Tcp_Message(msg,self.am_ip,self.bd_port)
                    else:
                        response = Tcp_Message(msg,self.sm_ip,self.bd_port)
                    #Enviar la respuesta
                    Udp_Message(response,ip,port)
                    print(response)
                    
                # Pedido desde un productor
                else:
                    #Mandar el update a la bd1
                    #Mandar el update a la bd2
                    #Tcp_Message(req,self.am_ip,self.bd_port)
                    Tcp_Message(req,self.sm_ip,self.bd_port)