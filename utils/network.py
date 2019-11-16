from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from json import dumps, loads
from threading import Thread,Semaphore
from inspect import signature

# decorador que reintenta una función si esta da error cada seconds cantidad de tiempo
def Retry(seconds):
    time_to_sleep = seconds
    def FReciever(function):
        objetive = function
        def wrapper(*args,**kwargs):
            try:
                return objetive(*args,**kwargs)
            except:
                sleep(time_to_sleep)
                return wrapper(*args,**kwargs)
        return wrapper
    return FReciever

# Funcion por defecto si no se quiere procesar el mesaje broadcast
def Void(socket):
    pass

# Función que envia un mensaje (en bytes) mediante  broadcast y devuelve el resultado de una función a la que se le pasa el socket
# Esta función no falla dado que siempre va a existir una interfaz a la cual entregar el socket, el manejo de errores se delega en la función a aplicar
def Send_Broadcast_Message(message, Broadcast_Address, Broadcast_Port, function = Void):
    broadcast = socket(type = SOCK_DGRAM)
    broadcast.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
    broadcast.sendto(message, (Broadcast_Address, Broadcast_Port))
    result = function(broadcast)
    broadcast.close()
    return result

#Codifica un diccionario en forma json para sen enviado por la red
def Encode_Request(dicc):
    return dumps(dicc).encode("utf-8")

#Decodifica la respusta en forma de json a un diccionario python
def Decode_Response(data):
    return loads(data)

#Dado un ip en string lo convierte a binario
def Ip_To_Binary(ip):
    octet_list = ip.split(".")
    octet_list_bin = [format(int(i),'08b') for i in octet_list]
    binary = ("").join(octet_list_bin)
    return binary

#Devuelve el numero del host dentro de la subnet dado un string (ip) y el numero de la mascara
def Get_Subnet_Host_Number(ip,mask):
    ip_bin = Ip_To_Binary(ip)
    host = ip_bin[mask:]
    return int(host)

#FIXME aplicar hilos para concurrencia y un lock

#Clase para el algoritmo de descubrimiento
class Discovering:
    def __init__(self, port,broadcast_addr,time = 10):
        self.partners = []
        self.port = port
        self.b_addr = broadcast_addr
        self.mutex = Semaphore()
        self.time = time
        self.socket = socket(type = SOCK_DGRAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
        self.socket.bind(('', port))

    def start(self):
        Thread(target=self._write, args=(self,),daemon=True).start()
        while True:
            msg, addr = self.socket.recvfrom(2048)
            Thread(target=self._listen, args=(self,addr[0],),daemon=True).start()
           
    # Hilo que va a recibir el mensaje de broadcast y procesarlo
    def _listen(self,ip):
        #FIXME hacer lock
        if ip not in self.partners:
            self.mutex.acquire()
            self.partners.append(ip)
            self.mutex.release()

    # Hilo que va a enviar cada cierto tiempo definido un mensaje broadcast para decir que esta vivo
    def _write(self):
        while True:
            Send_Broadcast_Message("Hello",self.b_addr,self.port,)
            sleep(self.time)
    

