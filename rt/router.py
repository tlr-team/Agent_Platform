from socket import scoket
from time import sleep
from json import loads, dumps
from threading import Thread, Semaphore
from queue import Queue
from utlis.network import Decode_Response,Encode_Request

# Clase base para el router
class Router:
    

    # Hilo que se va a conectar al mq para recbir un mensaje
    def _recieve(self):
        pass
