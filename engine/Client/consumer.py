from .config import Log_Path,Error_Path,Service_Port,Server_Port,Server_Ip, Broadcast_Address
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from ..utils.network import Send_Broadcast_Message, Encode_Request, Decode_Response, Retry
from threading import Thread,Semaphore

# hacer un pedido broadcast para determinar la lista de los servicios:
get_list_message = Encode_Request({ "get":"list" })
get_list_addr = Broadcast_Address
get_list_port = 10001

@Retry(4,"Fallo al obtener petición remota, reintentando")
def get_list(broadcast):
    msg, _ = broadcast.recvfrom(1024)
    return Decode_Response(msg)

# obtener la lista de servicios
service_list = Send_Broadcast_Message(get_list_message,get_list_addr,get_list_port,get_list)

# Método de interacción con el usuario
def UI():
    print("Bienvenido a la plataforma de agentes LR")
    print("Por favor seleccione el tipo de servicio al que se desea conectar:")
    for i,service in enumerate(service_list):
        print(f'[{i+1}] : {service}')
    total = len(service_list)
    user = 0
    while(not user):
        user = int(input("Escriba el numero del Servicio: "))
        if user >= 1 and user <= total:
            break
        else :
            user = 0
    return user

# Recurso buscado definido por el usuario
user_choice = service_list[UI()-1]
print("choice: ",user_choice)

get_request_message = Encode_Request({ "get": user_choice })
get_request_addr = get_list_addr
get_request_port = get_list_port

# Pedir el listado de posibles productores
def Get_request(broadcast):
    msg, _ = broadcast.recvfrom(1024)
    return Decode_Response(msg)

# Lista de productores pedida
producers = Send_Broadcast_Message(get_request_message, get_request_addr, get_request_port,Get_request)
print(producers)

# Estado de la petición
state = "Sin Terminar"

#Mientras hayan productores o no se haya terminado la petición del usuario intentar satisfacer el request
while(len(producers) and state == "Sin Terminar"):
    address = producers.pop()
    # Dirección del agente productor
    server = (address["ip"],address["port"])
    ConnectionType = address["stype"] # TCP o UDP


    # socket de servicio (local) "localhost:8000 para simplificar el acceso del cliente"
    local : socket

    if ConnectionType == "tcp": 
        local = socket(type = SOCK_STREAM)
        local.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
        local.bind(("127.0.0.1", Service_Port))
        local.listen(1)
    else:
        local = socket(type = SOCK_DGRAM)
        local.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
        local.bind(("127.0.0.1", Service_Port))


    # Server que hace forwarding de las peticiones a la interfaz local al servidor agente
    while True:
        msg : bytes
        if ConnectionType == "tcp":
            client, addr = local.accept()
            # recibir el pedido del socket local
            msg = client.recv(1024)
            #hilo tcp
            Thread(target=process_client_request, args=(ConnectionType,msg,addr,client),daemon=True).start()
        else:
            #hilo upd
            msg, addr = local.recvfrom(1024)
            Thread(target=process_client_request, args=(ConnectionType,msg,addr,),daemon=True).start()
        
    #FIXME hilo que chequee que el usuario no pare el proceso
    #state = "Terminado"
    
    local.close()

def process_client_request(ConnectionType, msg, addr, client = None):
    # socket que se va a conectar al agente
    cp = socket(type = SOCK_STREAM) if ConnectionType == "tcp" else socket(type=SOCK_DGRAM)

    msg : bytes
    addr : tuple

    if ConnectionType == "tcp":
        # enviar el request al productor (agente)
        cp.connect(server)
        cp.send(msg)
    else:
        cp.sendto(msg, server)
    
    # Leer la respuesta byte a byte para evitar problemas de bloqueo
    msgcp = cp.recv(1) if ConnectionType == "tcp" else cp.recvfrom(1024)[0]
    while(msgcp != b''):
        # enviar la respuesta al socket que originalmente hizo el request a la interfaz local (localhost:8000)
        client.send(msgcp) if ConnectionType == "tcp" else cp.sendto(msgcp, addr)
        print(msgcp)
        # continuar leyendo
        msgcp = cp.recv(1) if ConnectionType == "tcp" else cp.recvfrom(1)[0]
    
    # Cerrar los sockets tanto el remoto como el que responde a la petición local
    cp.close()
    client.close()