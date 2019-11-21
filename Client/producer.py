from .producer_options import Log_Path,Error_Path,Service_Port,Server_Port,Server_Ip
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR,SOCK_STREAM
from utils.network import Encode_Request, Decode_Response
from pathlib import Path
from yaml import load, FullLoader

server = (Server_Ip,Server_Port)
producers = []

agents = []

agent_directory = Path('/home/Agent')

for agent_config in agent_directory.iterdir():
    if agent_config.suffix == '.agent':
        with agent_config.open() as config:
            agents.append(load(config,FullLoader))

print(agents)
            