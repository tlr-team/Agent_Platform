from socket import (
    socket,
    SOCK_DGRAM,
    SOL_SOCKET,
    SO_REUSEADDR,
    SOCK_STREAM,
    SO_BROADCAST,
)
from ..utils.network import (
    Send_Broadcast_Message,
    Encode_Request,
    Decode_Response,
    retry,
    Udp_Message,
    Udp_Response,
)
from threading import Thread, Semaphore
from pathlib import Path
from yaml import load, FullLoader
from time import sleep
from random import randint

class PlatformInterface:
    def __init__(self , ip=None, mask=None):
        self.ip = ip
        self.mask = mask
    
    def register_agent(self, ip, port, url, protocol, name):
        '''
        Publicar Un Agente a la Plataforma
        '''
        pass

    def delete_agent(self, ip, port, url, protocol, name):
        '''
        Eliminar un agente de la plataforma
        '''
        pass

    def get_service_list(self, timeout=5):
        '''
        Obtener listado de servicios disponibles en la plataforma

        Devuelve una lista de strings si es posible conectar, None EOC
        '''
        try:
            service_list = []
            if len(self.attenders_list):
                with self.attenders_list_lock:
                    choice = randint(0, len(self.attenders_list) - 1)
                    service_list = Udp_Message(
                        {'get': 'list'},
                        self.attenders_list[choice],
                        PLATAFORM_PORT,
                        Udp_Response,
                    )
            return service_list
        except Exception as e:
            error(f'Unhandled Exception: {e}')
            return []

    def get_agent(self, service, timeout=5):
        '''
        Obtener un agente que cumple un servicio descrito en la plataforma

        Devuelve una descripción de un agente de ser posible, None EOC
        '''
        try:
            agent_list = []
            with self.attenders_list_lock:
                index = randint(0, len(self.attenders_list) - 1)
                agent_list = Udp_Message(
                    {'get': service},
                    self.attenders_list[index],
                    PLATAFORM_PORT,
                    Udp_Response,
                )
            return loads(agent_list[randint(0, len(agent_list) - 1)])
        except Exception as e:
            error(f'Unhandled Exception: {e}')
            return {}
