from cmd import Cmd
from threading import Lock, Thread
from pathlib import Path
from yaml import load, FullLoader
from random import randint
from time import sleep
from .. utils.network import Udp_Message, WhoCanServeMe_request, Get_Broadcast_Ip, Udp_Response, Send_Broadcast_Message, WhoCanServeMe_Response, Decode_Response
from socket import gethostbyname, socket, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET, SOCK_DGRAM

class Client(Cmd):

    def __init__(self, ip = None, mask = None, template_format = '.agent', template_path = '../Templates', agent_publish_time = 10, port = 10000, attender_refresh_time = 10):
        super(Client,self).__init__()
        self.service_list = []
        self.attenders_list = []
        self.attenders_list_lock = Lock()
        self.agent_list = []
        self.template_format = template_format
        self.template_path = template_path
        self.connection_port = port
        self.agent_publish_time = agent_publish_time
        self.attender_refresh_time = attender_refresh_time
        self.ip = ip
        self.mask = mask
        self.state = 0 # 0 non running, # 1 running (server)
        self.prompt = 'lragentplatform: '
        self.intro = "Bienvenidos a la plataforma de agentes LR, escriba ? para listar los comandos"

    def preloop(self):
        Thread(target=self._get_attenders, daemon=True).start()
        Thread(target=self._publish, daemon=True).start()
        Thread(target=self._discover_server, daemon=True).start()

    def do_get_service_list(self, arg):
        if len(self.attenders_list):
            with self.attenders_list_lock:
                choice = randint(0, len(self.attenders_list) -1)
                self.service_list = Udp_Message({'get':'list'}, self.attenders_list[choice], self.connection_port, Udp_Response)
        self.do_show_service_list(None)
    
    def do_show_service_list(self, arg):
        print('Service List: ')
        for i,name in enumerate(self.service_list):
            print(f'{i+1} : {name}')

    def do_connect(self, arg):
        self.state = 1
        Thread(target=self._serve, daemon=True).start()
        

    def do_show_atternder_list(self, arg):
        with self.attenders_list_lock:
            print(self.attenders_list)

    def do_get_agent_list(self, arg):
        try:
            with self.attenders_list_lock:
                choice = self.service_list[int(arg)-1]
                index = randint(0, len(self.attenders_list) -1)
                self.agent_list = Udp_Message({'get': choice}, self.attenders_list[index], self.connection_port, Udp_Response)
                self.do_show_agent_list(None)
        except:
            self.agent_list = []

    def do_show_agent_list(self, arg):
        print('Agent List: ')
        for i,name in enumerate(self.agent_list):
            print(f'{i+1} : {name}')

    def do_disconnect(self, arg):
        self.state = 0

    def _serve(self, ip='127.0.0.1', port=8888):
        if len(self.agent_list):
            agent = self.agent_list.pop()
            # Dirección del agente productor
            print('agent', agent)
            server = (agent["ip"], agent["port"])
            ConnectionType = agent["protocol"]  # TCP o UDP

            # socket de servicio (local) "localhost:8000 para simplificar el acceso del cliente"
            local :socket

            local = socket(type=SOCK_STREAM if ConnectionType == 'TCP' else SOCK_DGRAM)
            local.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            local.bind((ip, port))
            local.settimeout(5)

            if ConnectionType == "TCP":
                local.listen(1)

            # Server que hace forwarding de las peticiones a la interfaz local al servidor agente
            while self.state:
                try:
                    msg: bytes
                    if ConnectionType == "TCP":
                        client, addr = local.accept()
                        # recibir el pedido del socket local
                        msg = client.recv(1024)
                        # hilo TCP
                        Thread(
                            target=process_client_request,
                            args=(ConnectionType, msg, addr, server, client),
                            daemon=True,
                        ).start()
                    else:
                        # hilo upd
                        msg, addr = local.recvfrom(1024)
                        Thread(
                            target=process_client_request,
                            args=(ConnectionType, msg, addr, server),
                            daemon=True,
                        ).start()
                except:
                    pass
            # FIXME hilo que chequee que el usuario no pare el proceso
            # state = "Terminado"
            print("SERVER CERRANDO")
            local.close()

    def _publish(self):
        while(True):
            self.template_list = self._load_templates()
            for service in self.template_list:
                with self.attenders_list_lock:
                    if len(self.attenders_list):
                        index = randint(0, len(self.attenders_list)-1)
                        choice = self.attenders_list[index]
                        msg = {'post': service['service'], 'ip':service['ip'], 'port': service['port'], 'url' : service['url'], 'protocol': service['protocol']}
                        ans = Udp_Message(msg, choice, self.connection_port)
                        if not ans:
                            self.attenders_list.pop(index)
            sleep(self.agent_publish_time)
    
    def _get_attenders(self):
        while(True):
            if self.ip and self.mask:
                Thread(target=Send_Broadcast_Message, args=({'WHOCANSERVEME':''}, Get_Broadcast_Ip(self.ip, self.mask), self.connection_port), daemon=True).start()

            for i in ['m1.lragentplatfrom.grs.uh.cu','m2.lragentplatfrom.grs.uh.cu']:
                try:
                    with self.attenders_list_lock:
                        newone = gethostbyname(i)
                        if not newone in self.attenders_list:
                            self.attenders_list.append()
                except:
                    pass
            sleep(self.attender_refresh_time)

    def _discover_server(self):
        with socket(type=SOCK_DGRAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            sock.bind(('', 10003))
            while(True):
                msg, addr = sock.recvfrom(1024)
                post = Decode_Response(msg)
                if 'ME' in post:
                    with self.attenders_list_lock:
                        if not addr[0] in self.attenders_list:
                            self.attenders_list.append(addr[0])


    def _load_templates(self):
        # Directorio donde se encentran las planillas de los agentes
        agent_directory = Path(self.template_path)

        # Listado de agentes en la carpeta de configuracion
        agents = []

        for agent_config in agent_directory.iterdir():
            if agent_config.suffix == self.template_format:
                with agent_config.open() as config:
                    # cada planilla esta en formato yaml
                    agents.append(load(config, FullLoader))

        return agents

def process_client_request(ConnectionType, msg, addr, server, client=None):
    # socket que se va a conectar al agente
    with socket(type=SOCK_STREAM) if ConnectionType == "TCP" else socket(
        type=SOCK_DGRAM
    ) as cp:
        msg: bytes
        addr: tuple
        
        print(f'Connection from {server}, {msg}')

        if ConnectionType == "TCP":
            # enviar el request al productor (agente)
            cp.connect(server)
            cp.send(msg)
        else:
            cp.sendto(msg, server)

        # Leer la respuesta byte a byte para evitar problemas de bloqueo
        msgcp = cp.recv(1) if ConnectionType == "TCP" else cp.recvfrom(1024)[0]
        while msgcp != b'':
            # enviar la respuesta al socket que originalmente hizo el request a la interfaz local (localhost:8000)
            client.send(msgcp) if ConnectionType == "TCP" else cp.sendto(msgcp, addr)
            print(msgcp)
            # continuar leyendo
            msgcp = cp.recv(1) if ConnectionType == "TCP" else cp.recvfrom(1024)[0]
        
    if client:
        client.close()
