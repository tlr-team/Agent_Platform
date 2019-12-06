from socket import (
    socket,
    SOCK_DGRAM,
    SOL_SOCKET,
    SO_REUSEADDR,
    SOCK_STREAM,
    SO_BROADCAST,
)
from time import sleep
from json import dumps, loads
from threading import Thread, Semaphore
from inspect import signature
from io import BytesIO

# decorador que reintenta una función si esta da error cada seconds cantidad de tiempo
def Retry(seconds, message = 'No es posible conectar, reintentando'):
    time_to_sleep = seconds

    def FReciever(function):
        objetive = function

        def wrapper(*args, **kwargs):
            try:
                return objetive(*args, **kwargs)
            except:
                sleep(time_to_sleep)
                print(message)
                return wrapper(*args, **kwargs)

        return wrapper

    return FReciever

# Funcion por defecto si no se quiere procesar el mesaje broadcast
def Void(socket):
    pass


# Función que envia un mensaje (en bytes) mediante  broadcast y devuelve el resultado de una función a la que se le pasa el socket
# Esta función no falla dado que siempre va a existir una interfaz a la cual entregar el socket, el manejo de errores se delega en la función a aplicar
def Send_Broadcast_Message(message, Broadcast_Address, Broadcast_Port, function = Void, timeout = 5):
    try:
        with socket(type = SOCK_DGRAM) as broadcast:
            broadcast.settimeout(timeout)
            broadcast.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
            broadcast.sendto(Encode_Request(message), (Broadcast_Address, Broadcast_Port))
            result = function(broadcast)
    except:
        result = ''
    return result


# Codifica un diccionario en forma json para sen enviado por la red
def Encode_Request(dicc):
    return dumps(dicc).encode("utf-8")


# Decodifica la respusta en forma de json a un diccionario python
def Decode_Response(data):
    return loads(data)


# Dado un ip en string lo convierte a binario
def Ip_To_Binary(ip):
    octet_list = ip.split(".")
    octet_list_bin = [format(int(i), '08b') for i in octet_list]
    binary = ("").join(octet_list_bin)
    return binary


# Devuelve el numero del host dentro de la subnet dado un string (ip) y el numero de la mascara
def Get_Subnet_Host_Number(ip, mask):
    ip_bin = Ip_To_Binary(ip)
    host = ip_bin[mask:]
    result = 0
    for i in range(0,len(host)):
        if int(host[i]):
            result += 2 ** (len(host)-i-1) 
    return result

# Convierte un ip de binario a notecion decimal ipv4
def Binary_To_Ip(binary):
    dec_list = []
    suma = 0
    size = len(binary)
    for i in range(0,size):
        t = int(binary[size-i-1])
        if t:
            suma += 2**(i%8)
        if i%8 == 7:
            dec_list.append(str(suma))
            suma = 0
    if suma > 0:
        dec_list.append(str(suma))
    return '.'.join(i for i in dec_list[::-1])

# Calcula la dirección broadcast de la subred
def Get_Broadcast_Ip(ip, mask):
    ip_bin = Ip_To_Binary(ip)
    network = ip_bin[:mask]
    network += '1' * (32-mask)
    return Binary_To_Ip(network)

# Recive un socket TCP y devuelve el resultado de leer todo el contenido del mismo
def Tcp_Sock_Reader(sock):
    result = None
    with BytesIO() as buf:
        msg = sock.recv(1)
        llaves = 1 if msg in b'{[' else 0
        if llaves:
            buf.write(msg)
            comillas = False
            while llaves:
                msg = sock.recv(1)
                buf.write(msg)
                if msg == b'"':
                    comillas = not comillas
                if msg in b'{['  and not comillas:
                    llaves += 1
                if msg in b'}]' and not comillas:
                    llaves -= 1
            result = Decode_Response(buf.getvalue())
    return result

#Envia un mensaje tcp y devuelve la respuesta
def Tcp_Message(msg,ip,port, function = Tcp_Sock_Reader):
    with socket(type= SOCK_STREAM) as sock:
        sock.connect((ip,port))
        tmp = Encode_Request(msg)
        sock.send(tmp)
        response = function(sock)
    return response


# Envia un mensaje udp
def Udp_Message(msg, ip, port, function = Void):
    with socket(type=SOCK_DGRAM) as sock:
        sock.sendto(Encode_Request(msg), (ip, port))
        return function(sock)

def Udp_Response(socket):
    return Decode_Response(socket.recvfrom(2048)[0])

def ServerTcp(ip, port, client_fucntion, logger, Stop_Condition = False, objeto = None):
    with socket(type=SOCK_STREAM) as sock:
        sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,True)
        sock.listen(10)
        while(True):
            if(objeto and Stop_Condition(objeto)):
                break
            client, addr = sock.accept()
            logger.debug(f'Recieved TCP Connection from f{addr}')
            Thread(target=client_fucntion,args=(client,addr),daemon=True).start()

def ServerUdp(ip, port, client_fucntion, logger, Stop_Condition = False, objeto = None):
    with socket(type=SOCK_DGRAM) as sock:
        sock.setsockopt(SOL_SOCKET,SO_REUSEADDR,True)
        while(True):
            if(objeto and Stop_Condition(objeto)):
                break
            msg, addr = sock.recvfrom(1024)
            logger.debug(f'Recieved UDP Connection from f{addr}')
            Thread(target=client_fucntion,args=(msg,addr),daemon=True).start()


# FIXME aplicar hilos para concurrencia y un lock

# Clase para el algoritmo de descubrimiento
class Discovering:
    def __init__(self, port, broadcast_addr, logger, time=10, ttl = 3):
        self.partners = {}
        self.port = port
        self.b_addr = broadcast_addr
        self.mutex = Semaphore()
        self.time = time
        self.ttl = ttl
        self.socket = socket(type=SOCK_DGRAM)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
        self.socket.bind(('', port))
        self.logger = logger
        self.logger.info(f'Discover Server Initiated at f{port}')
        Thread(target=self._start,daemon=True,name='DiscoverServer')

    def Get_Partners(self):
        with self.mutex:
            return [a for a in self.partners.keys()]

    def _start(self):
        Thread(target=self._write, daemon=True).start()
        Thread(target=self._refresh, daemon=True).start()
        while True:
            _, addr = self.socket.recvfrom(1024)
            self.logger.debug(f'Discovering:  Recieved connection from {addr}')
            Thread(target=self._listen, args=(addr[0],), daemon=True).start()

    # Hilo que va a recibir el mensaje de broadcast y procesarlo
    def _listen(self, ip):
        if ip not in self.partners:
            with self.mutex:
                self.partners[ip] = self.ttl

    # Hilo que va a enviar cada cierto tiempo definido un mensaje broadcast para decir que esta vivo
    def _write(self):
        self.logger.info(f'Discover write Daemon initiated')
        while True:
            Send_Broadcast_Message("Hello", self.b_addr, self.port)
            sleep(self.time)

    #Hilo que va a refrescar el estado de la tabla
    def _refresh(self):
        self.logger.info(f'Discover refresh Daemon initiated')
        while(True):
            with self.mutex:
                temp = {}
                for name, val in self.partners.items():
                    if val > 1:
                        temp[name] = val - 1
                self.partners = temp
            sleep(self.time)

