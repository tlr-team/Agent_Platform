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
    Udp_Response
)
from io import BytesIO

# Funcionamiento del Router:
# Hilo1 busca un listado de mq (similar al cliente) y pide un request y lo encola en una lista si esta esta vacia (ojo, semaforo)
# Hilo2 desencola el request si existe , lo procesa y se conecta finalmente con el cliente con el resultado final

# Clase base para el router
class Router:
    def __init__(self):
        # mutex
        self.channel = []
        self.mutex = Semaphore()
        self.Broadcast_Address = "192.168.2.31"
        self.Broadcast_Port = 10002
        self.am_ip = "127.0.0.1"
        self.sm_ip = "192.168.2.7"
        self.bd_port = 9342

    def serve(self):
        Thread(target=self._recieve,daemon=True,name="recieve").start()
        Thread(target=self._resolve,daemon=True,name="resolve").start()
        while(True):
            sleep(5)
        

    # Hilo que se va a conectar al mq para recbir un mensaje
    def _recieve(self):
        while(True):
            result = Send_Broadcast_Message('get',self.Broadcast_Address,self.Broadcast_Port,Udp_Response)

            if result and not len(self.channel):
                with self.mutex:
                    message = result
                    print(message)
                    self.channel.append(message)

            else:
                sleep(5)

    # Hilo que va a procesar el pedido
    def _resolve(self):
        ''' Hilo que va a procesar el pedido '''
        while(True):
            self.mutex.acquire()
            if not len(self.channel):
                self.mutex.release()
                sleep(5)
            else:
                print('channel',self.channel)
                req = self.channel.pop()
                self.mutex.release()
                # Pedido desde un cliente
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
            

Router().serve()
