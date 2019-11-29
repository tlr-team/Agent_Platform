from .producer_options import Log_Path,Error_Path,Service_Port,Server_Port,Server_Ip
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR,SOCK_STREAM
from utils.network import Encode_Request, Decode_Response
from pathlib import Path
from yaml import load, FullLoader

server = (Server_Ip,Server_Port)
producers = []

def load_config(path, format = '.agent'):
    #Directorio donde se encentran las planillas de los agentes
    agent_directory = Path(path)

    #Listado de agentes en la carpeta de configuracion
    agents = []

    for agent_config in agent_directory.iterdir():
        if agent_config.suffix == format:
            with agent_config.open() as config:
                #cada planilla esta en formato yaml
                agents.append(load(config,FullLoader))

    return agents
            