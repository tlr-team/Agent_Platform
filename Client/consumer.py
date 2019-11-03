from config import Log_Path,Error_Path,Service_Port,Server_Port,Server_Ip, Broadcast_Address
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from json import dumps, loads

# hacer un pedido broadcast para determinar la lista de los servicios:
def get_list():
    broadcast = socket(type = SOCK_DGRAM)
    broadcast.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
    message = { "get":"list" }
    broadcast.sendto(dumps(message).encode("utf-8"), (Broadcast_Address, 10001))
    msg, addr = broadcast.recvfrom(1024)
    return loads(msg)

# obtener la lista de servicios
service_list = get_list()

# Método de interacción con el usuario
def UI():
    print("Bienvenido a la plataforma de agentes LR")
    print("Por favor seleccione el tipo de servicio al que se desea conectar:")
    for i,service in enumerate(service_list):
        print(f'[{i+1}] : {service}')
    total = len(service)
    user = 0
    while(not user):
        user = int(input("Escriba el numero del Servicio"))
        if user >= 1 and user <= total:
            break
        else :
            user = 0
    return user

# Recurso buscado definido por el usuario
user_choice = service_list[UI()-1]

# Pedido a la plataforma
request = { "get", user_choice }

# Pedir el listado de posibles productores
def Get_request():
    broadcast = socket(type = SOCK_DGRAM)
    broadcast.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
    message = { "get":request }
    broadcast.sendto(dumps(message).encode("utf-8"), (Broadcast_Address, 10001))
    msg, addr = broadcast.recvfrom(1024)
    return loads(msg)

# Lista de productores pedida
producers = Get_request()

# Estado de la petición
state = "Sin Terminar"

# socket de servicio (local) "localhost:8000 para simplificar el acceso del cliente"
local = socket(type = SOCK_STREAM)
local.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
local.listen(1)
local.bind(('localhost', Service_Port))


#Mientras hayan productores o no se haya terminado la petición del usuario intentar satisfacer el request
while(len(producers) or state == "Sin Terminar"):
    address = producers.pop()
    # Dirección del agente productor
    server = (address["ip"],address["port"])
    ConnectionType = address["stype"] # TCP o UDP

    # Server que hace forwarding de las peticiones a la interfaz local al servidor agente
    while True:
        client, addr = local.accept()
        # recibir el pedido del socket local
        msg = client.recv(1024)
        # socket que se va a conectar al agente
        cp = socket(type = SOCK_STREAM) if ConnectionType == "TCP" else socket(type=SOCK_DGRAM)

        msg : bytes
        addr : tuple

        if ConnectionType == "TCP":
            # enviar el request al productor (agente)
            cp.connect(server)
            cp.send(msg)
        else:
            cp.sendto(msg, server)
        
        # Leer la respuesta byte a byte para evitar problemas de bloqueo
        msgcp = cp.recv(1) if ConnectionType == "TCP" else cp.recvfrom(1)[0]
        while(msgcp != b''):
            # enviar la respuesta al socket que originalmente hizo el request a la interfaz local (localhost:8000)
            client.send(msgcp)
            print(msgcp)
            # continuar leyendo
            msgcp = cp.recv(1) if ConnectionType == "TCP" else cp.recvfrom(1)[0]
        
        # Cerrar los sockets tanto el remoto como el que responde a la petición local
        cp.close()
        client.close()