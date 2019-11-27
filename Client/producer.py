from producer_options import Log_Path,Error_Path,Service_Port,Server_Port,Server_Ip
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR,SOCK_STREAM
from network import Encode_Request, Decode_Response, Send_Broadcast_Message
from pathlib import Path
from yaml import load, FullLoader
from time import sleep

server = (Server_Ip,Server_Port)
producers = []

def load_config(path, formato = '.agent'):
    #Directorio donde se encentran las planillas de los agentes
    agent_directory = Path(path)

    #Listado de agentes en la carpeta de configuracion
    agents = []

    for agent_config in agent_directory.iterdir():
        if agent_config.suffix == formato:
            with agent_config.open() as config:
                #cada planilla esta en formato yaml
                agents.append(load(config,FullLoader))

    return agents

lista = load_config("/home/rmarti/templates")
print(lista)

while(True):
    for prod in lista:
        msg = {"post":prod["service"]}
        for i in prod.keys():
            if i != 'service':
                msg[i] = prod[i]
        Send_Broadcast_Message(msg,"10.10.10.255",10001,)
        print(msg, "sended to broadcast")
    sleep(5)
            