from config import Log_Path,Error_Path,Service_Port,Server_Port,Server_Ip
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from json import dumps, loads

# Estado del cliente 1, 2, 3
state = 1
# Pedido a la plataforma
request = {}
# Dirección del servidor de la plataforma de agentes
server = (Server_Ip,Server_Port)
# Lista de productores pedida
producers = []
# Recurso buscado definido por el usuario
Resource = "A"
# Tipo de connección al agente final (UDP / TCP)
ConnectionType = "UDP"

# Hacer pedido broadcast para detectar el server
broadcast = socket(type = SOCK_DGRAM)
broadcast.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
broadcast.sendto(b'Hello', ('192.168.2.255', 10001))
msg, addr = broadcast.recvfrom(1024)
result = loads(msg)
print(result)

exit()

# socket de servicio (local) "localhost:8000 para simplificar el acceso del cliente"
local = socket(type = SOCK_STREAM)
local.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
local.listen(1)
local.bind(('localhost', Service_Port))



# Server que hace forwarding de las peticiones a la interfaz local al servidor agente
while True:
    client, addr = local.accept()
    # socket que se va a conectar al agente
    cp = socket(type = SOCK_STREAM) if ConnectionType == "TCP" else socket(type=SOCK_DGRAM)
    # recibir el pedido del socket local
    msg = client.recv(1024)
    print(msg)
    # enviar el request al productor (agente)
    cp.connect(server)
    cp.send(msg)
    # Leer la respuesta byte a byte para evitar problemas de bloqueo
    msgcp = cp.recv(1)
    while(msgcp != b''):
        # enviar la respuesta al socket que originalmente hizo el request a la interfaz local (localhost:8000)
        client.send(msgcp)
        print(msgcp)
        # continuar leyendo
        msgcp = cp.recv(1)
    # Cerrar los sockets tanto el remoto como el que responde a la petición local
    cp.close()
    client.close()


# def Get_Data(s):
#     msg, addr = s.recvfrom(2048)
#     producers = loads(msg)


# def Connect_To_Cp(Cpip,cpport):
