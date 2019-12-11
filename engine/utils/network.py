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
from functools import wraps
from hashlib import sha1


def get_hash(addr=None, ip='', port=''):
    addr = addr or (ip, port)
    assert addr[0] and addr[1]
    return int(sha1((':'.join((addr[0], str(addr[1])))).encode()).hexdigest(), base=16)


# decorador que reintenta una función si esta da error cada seconds cantidad de tiempo
def retry(time_to_sleep, times=1, message='No es posible conectar, reintentando'):
    def FReciever(function):
        @wraps
        def wrapper(*args, **kwargs):
            count = 0
            while times > count:
                try:
                    result = function(*args, **kwargs)
                    return True, result
                except:
                    # logger.error(message)
                    if times <= count + 1 and time_to_sleep:
                        sleep(time_to_sleep)
                count += 1
            return False, None

        return wrapper

    return FReciever


# Funcion por defecto si no se quiere procesar el mesaje broadcast
def Void(socket):
    pass


# Función que envia un mensaje (en bytes) mediante  broadcast y devuelve el resultado de una función a la que se le pasa el socket
# Esta función no falla dado que siempre va a existir una interfaz a la cual entregar el socket, el manejo de errores se delega en la función a aplicar
def Send_Broadcast_Message(
    message, Broadcast_Address, Broadcast_Port, function=Void, timeout=5
):
    try:
        with socket(type=SOCK_DGRAM) as broadcast:
            broadcast.settimeout(timeout)
            broadcast.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
            broadcast.sendto(
                Encode_Request(message), (Broadcast_Address, Broadcast_Port)
            )
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
    for i in range(0, len(host)):
        if int(host[i]):
            result += 2 ** (len(host) - i - 1)
    return result


# Convierte un ip de binario a notecion decimal ipv4
def Binary_To_Ip(binary):
    dec_list = []
    suma = 0
    size = len(binary)
    for i in range(0, size):
        t = int(binary[size - i - 1])
        if t:
            suma += 2 ** (i % 8)
        if i % 8 == 7:
            dec_list.append(str(suma))
            suma = 0
    if suma > 0:
        dec_list.append(str(suma))
    return '.'.join(i for i in dec_list[::-1])


# Calcula la dirección broadcast de la subred
def Get_Broadcast_Ip(ip, mask):
    ip_bin = Ip_To_Binary(ip)
    network = ip_bin[:mask]
    network += '1' * (32 - mask)
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
                if msg in b'{[' and not comillas:
                    llaves += 1
                if msg in b'}]' and not comillas:
                    llaves -= 1
            result = Decode_Response(buf.getvalue())
    return result

#Envia un mensaje tcp y devuelve la respuesta
def Tcp_Message(msg,ip,port, function = Tcp_Sock_Reader):
    with socket(type= SOCK_STREAM) as sock:
        try:
            sock.connect((ip,port))
            tmp = Encode_Request(msg)
            sock.send(tmp)
            response = function(sock)
        except Exception as e:
            return None
    return response


# Envia un mensaje udp
def Udp_Message(msg, ip, port, function=Void):
    with socket(type=SOCK_DGRAM) as sock:
        try:
            sock.sendto(Encode_Request(msg), (ip, port))
        except:
            return None
        return function(sock)


def Udp_Response(socket):
    return Decode_Response(socket.recvfrom(2048)[0])

def Udp_Full_Response(socket):
    return Decode_Response(socket.recvfrom(1024))

def ServerTcp(ip, port, client_fucntion, logger, Stop_Condition = False, objeto = None, lock = None):
    logger.info(f"Server TCP initiated at {ip,port}")
    with socket(type=SOCK_STREAM) as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
        sock.bind((ip, port))
        sock.listen(10)
        while(True):
            if objeto and (Stop_Condition(objeto) if not lock else Stop_Condition(objeto,lock)):
                logger.info("NO server anymore")
                break
            #print("Condicion TCP: ", Stop_Condition(objeto) if objeto != None else None)
            client, addr = sock.accept()
            logger.debug(f'Recieved TCP Connection from {addr}')
            Thread(target=client_fucntion, args=(client, addr), daemon=True).start()


def ServerUdp(ip, port, client_fucntion, logger, Stop_Condition=False, objeto=None):
    with socket(type=SOCK_DGRAM) as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
        sock.bind((ip, port))
        while True:
            if objeto and Stop_Condition(objeto):
                break
            msg, addr = sock.recvfrom(1024)
            #logger.debug(f'Recieved UDP Connection from {addr}')
            Thread(target=client_fucntion,args=(msg,addr),daemon=True).start()


def WhoCanServeMe(broadcast_addr, port, data_container, lock):
    while(True):
        answer = Send_Broadcast_Message({'WHOCANSERVEME':''}, broadcast_addr, port, Udp_Full_Response)
        if answer != '':
            with lock:
                data_container.append(answer[1][0])
        sleep(5)

def WhoCanServeMe_Server(port, client_fucntion, logger, stop_condition=False, objeto=None):
    ServerUdp('',port, client_fucntion, logger , stop_condition, objeto)

def WhoCanServeMe_client(msg, addr):
    Udp_Message({'ME':''}, addr[0], addr[1])