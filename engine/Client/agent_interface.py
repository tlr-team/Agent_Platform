from .config import Log_Path,Error_Path,Service_Port,Server_Port,Server_Ip, Broadcast_Address
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from ..utils.network import Send_Broadcast_Message, Encode_Request, Decode_Response, Retry, Discovering, Udp_Message, Upd_Response
from threading import Thread,Semaphore
from pathlib import Path
from yaml import load, FullLoader
from time import sleep
from random import randint

def recive_help(socket):
    '''
    recive pedidos udp por un tiempo
    '''
    socket.listen(5)
    result = []
    for _ in range(0,6):
        result.append(socket.recvfrom(1024)[1][0])
        sleep(2)
    
    return result
    


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

def process_client_request(ConnectionType, msg, addr, server, client = None):
    # socket que se va a conectar al agente
    with socket(type = SOCK_STREAM) if ConnectionType == "tcp" else socket(type=SOCK_DGRAM) as cp:
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
            msgcp = cp.recv(1) if ConnectionType == "tcp" else cp.recvfrom(1024)[0]
        

@Retry(4,"Fallo al obtener petición remota, reintentando")
def get_list(broadcast):
    msg, _ = broadcast.recvfrom(1024)
    return Decode_Response(msg)

#FIXME Parametrizar todas las opciones
class Agent_Interface:
    '''
    Clase cuya funcionalidad es la de brindar la de interfaz de la plataforma
    Tiene dos funcionalidades principales, la de hacer de publisher de agentes y
    la de interfaz local de comunicacion
    '''
    
    def __init__(self, template_path = "../Templates"):
        self.discover = Discovering(Server_Port,Broadcast_Address,time=20)
        self.template_path = template_path
        self._renew_list()
        self.service_list = []
        self.attenders_list = []
        self.agent_list = []
        self.discover._start()


    #Hilo que va a publicar todos los agentes en la ruta local

    #region publisher

    def _publish_agents(self, time_to_sleep = 5):
        while(True):
            for prod in self.service_list:
                msg = {"post":prod["service"]}
                for i in prod.keys():
                    if i != 'service':
                        msg[i] = prod[i]
                Send_Broadcast_Message(msg,Broadcast_Address,Server_Port,)
                print(msg, "sended to broadcast")
            sleep(time_to_sleep)

    def _get_service_list(self, get_list_addr = Broadcast_Address, get_list_port = Server_Port, get_list_message = {"get":"list"}):
        self.service_list = Send_Broadcast_Message(get_list_message,get_list_addr,get_list_port,get_list,0)

    def _renew_list(self):
        self.agent_list = load_config(self.template_path)
    
    #endregion

    #region client interface
    def UI(self):
        print("Bienvenido a la plataforma de agentes LR")
        while(True):
            self._ui()
            self._serve()

    def _ui(self):
        print("Por favor seleccione el tipo de servicio al que se desea conectar:")
        self.service_list = self._send_request({"get":"list"})
        service = self._print_service_list()
        self.agent_list = self._send_request({"get": service})    

        
    def _print_service_list(self):
        '''
        Imprime en pantalla el listado de servicios conodidos
        Devuelve el indice del servicio seleccionado
        '''
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
        return user-1

    @Retry(10)
    def _send_request(self,msg):
        choice = randint(0,len(self.discover.partners))
        ip = self.discover.partners.keys()[choice]
        return Udp_Message(msg, ip, Server_Port, Upd_Response)

    def _serve(self):
        #state = "Running"
        if(len(self.agent_list)):
            address = self.agent_list.pop()
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
                    Thread(target=process_client_request, args=(ConnectionType,msg,addr,server,client),daemon=True).start()
                else:
                    #hilo upd
                    msg, addr = local.recvfrom(1024)
                    Thread(target=process_client_request, args=(ConnectionType,msg,server,addr,),daemon=True).start()
                
            #FIXME hilo que chequee que el usuario no pare el proceso
            #state = "Terminado"
            
            local.close()




    #endregion


