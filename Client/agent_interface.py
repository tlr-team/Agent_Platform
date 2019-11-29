from config import Log_Path,Error_Path,Service_Port,Server_Port,Server_Ip, Broadcast_Address
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from utils.network import Send_Broadcast_Message, Encode_Request, Decode_Response, Retry
from threading import Thread,Semaphore
from pathlib import Path
from yaml import load, FullLoader
from time import sleep

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

@Retry(4,"Fallo al obtener petición remota, reintentando")
def get_list(broadcast):
    msg, addr = broadcast.recvfrom(1024)
    return Decode_Response(msg)

#FIXME Parametrizar todas las opciones
class Agent_Interface:
    
    def __init__(self,  ,  template_path = "../Templates"):
        self.agent_list = load_config(template_path)
        self.service_list = []


    #Hilo que va a publicar todos los agentes en la ruta local
    def _publish_agents(self, time_to_sleep = 5):
        while(True):
            for prod in lista:
                msg = {"post":prod["service"]}
                for i in prod.keys():
                    if i != 'service':
                        msg[i] = prod[i]
                Send_Broadcast_Message(msg,"10.10.10.255",10001,)
                print(msg, "sended to broadcast")
            sleep(time_to_sleep)

    def _get_service_list(self, get_list_addr = "10.10.10.255", get_list_port = 10001, get_list_message = {"get":"list"}):
        self.service_list = Send_Broadcast_Message(get_list_message,get_list_addr,get_list_port,get_list,0)
    
    def _ui(self):
        print("Bienvenido a la plataforma de agentes LR")
        print("Por favor seleccione el tipo de servicio al que se desea conectar:")
        for i,service in enumerate(self.service_list):
            print(f'[{i+1}] : {service}')
        total = len(service)
        user = 0
        while(not user):
            user = int(input("Escriba el numero del Servicio: "))
            if user >= 1 and user <= total:
                break
            else :
                user = 0
        return user


