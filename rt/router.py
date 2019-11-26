from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from json import loads, dumps
from threading import Thread, Semaphore
from queue import Queue
from utils.network import Decode_Response,Encode_Request,Send_Broadcast_Message,Sock_Reader,Tcp_Message
from io import BytesIO

# Funcionamiento del Router:
# Hilo1 busca un listado de mq (similar al cliente) y pide un request y lo encola en una lista si esta esta vacia (ojo, semaforo)
# Hilo2 desencola el request si existe , lo procesa y se conecta finalmente con el cliente con el resultado final

# Clase base para el router
class Router:

    def __init__(self):
        #mutex 
        self.channel = []
        self.mutex = Semaphore()
        self.Broadcast_Address = ""
        self.Broadcast_Port = 8900
        Thread(target=self._recieve,deamon=True).start()
        Thread(target=self._resolve,deamon=True).start()

    # Hilo que se va a conectar al mq para recbir un mensaje
    def _recieve(self):
        while(True):
            result = Send_Broadcast_Message(Encode_Request({"get":"work"}),self.Broadcast_Address,self.Broadcast_Port,)

            if result != None and not len(self.channel):
                self.mutex.acquire()
                self.channel.append(Decode_Response(result))
                self.mutex.release()

            else:
                sleep(5)

    # Hilo que va a procesar el pedido
    def _resolve(self):
        ''' Hilo que va a procesar el pedido '''
        while(True):
            self.mutex.acquire
            if not len(self.channel):
                self.mutex.release() 
                sleep(5)
            else:
                req = self.channel.pop()
                self.mutex.release() 
                # Pedido desde un cliente
                if "get" in req.keys():
                    pass
                # Pedido desde un productor
                else:
                    #FIXME encapsular el metodo de comunicarse
                    Tcp_Message(req,"10.10.10.5",10003)
                pass
            
