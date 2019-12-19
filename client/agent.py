from rpyc import Service, connect
from inspect import isfunction, getfullargspec
from rpyc.utils.server import ThreadedServer
from threading import Thread, Lock
from engine.utils.logger import setup_logger, debug, error, info
from engine.utils.network import Udp_Message, Send_Broadcast_Message, Get_Broadcast_Ip
from socket import socket, SO_REUSEADDR, SOL_SOCKET, SOCK_DGRAM

setup_logger(name='AgentService')


def get_funcargs(func):
    args = getfullargspec(func).args
    return args[1:] if 'self' == args[0] else args


class AgentService(rpyc.Service):
    def __init__(self, ip = None, mask=None, port=None):
        self.ip = ip
        self.mask = mask
        self.port = port
        self.attenders_list = []
        self.attenders_list_lock = Lock()

    def exposed_sum(self, a, b):
        ''' Suma dos enteros y retorna la suma. '''
        return a + b
    
    def _connect_to(self, addr_ag):
        debug(f'trying to establish connection to {addr_ag}.')
        try:
            connection = connect(*addr_ag, config={'timeout': 2})
            debug(f'pinging (with rpyc_connection) to: {addr_ag}')
            connection.ping()
            debug(f'connected to agent at: {addr_ag}')
        except Exception as e:
            error(e)
        return connection

    def execute(self, service_name, func_name, *args):
        ''' 
            With a given service name and function name
            search for the available agents and execute 
            the function `func_name` in one of those agents. 
        '''
        debug(f'trying to execute in some agent with service: {service_name} the function named: {func_name}({args})')
        while True:
            try:
                agents = self._get_service(service_name)
                break
            except Exception as e:
                error(f'exception:{e}')
            debug('retrying to get_service')
            sleep(0,5)
        info(f'available agents: {agents}')
        while agents:
            try:
                cur_agent = agents.pop()
                _info = self._agent_info(cur_agent['ip'], cur_agent['port'])
                debug(f'trying with ,{cur_agent}, info: {_info}')
                if func_name in _info and (_info.get('args', None)) == len(args):
                    c = self._connect_to(cur_agent['ip'], cur_agent['port'])
                    if c!= None:
                        try:
                            res = c.root.__getattr__(func_name)(*args)
                            debug(f'Remote function call was executed with result: {res}')
                            return res
                        except Exception as e:
                            error(f'Remote function call interrupted because: {e}')
                            continue
            except:
                if agents:
                    debug('Trying with another agent')
        debug('the remote function could not be executed')
        return None
    
    @staticmethod
    def _service_name(cls):
        return cls.__name__.split('Service')[0]

    @staticmethod
    def _get_exposed_info(cls):
        funcs_exposed = {}
        for attr_name, attr in cls.__dict__.items():
            if (
                isfunction(attr)
                and attr_name.startswith('exposed_')
                and attr_name != 'exposed_'
            ):
                funcs_exposed[attr_name.split('exposed_')[1]] = {
                    'info': attr.__doc__,
                    'args': get_funcargs(attr),
                }
        return funcs_exposed

    def _publish_service(self):
        while(True):
            method_info = AgentService._get_exposed_info(self.__class__)
            service = AgentService.service_name(self.__class__)
            msg = { 'post': service,  'ip': self.ip,  'port': self.port,  'info': method_info }

            self.attenders_list_lock.acquire()
            if len(self.attenders_list):
                index = randint(0, len(self.attenders_list) - 1)
                choice = self.attenders_list[index]
                self.attenders_list_lock.release()    
                ans = Udp_Message(msg, choice, self.connection_port)
                    if not ans:
                        with self.attenders_list_lock:
                            self.attenders_list.pop(index)
            sleep(self.agent_publish_time)

    def _refresh_attenders(self):
        with socket(type=SOCK_DGRAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            sock.bind(('', 10004))
            while True:
                msg, addr = sock.recvfrom(1024)
                debug(f'MESSAGE FROM {addr}')
                post = Decode_Response(msg)
                if 'ME' in post:
                    with self.attenders_list_lock:
                        if not addr[0] in self.attenders_list:
                            debug(f'ATTENDER LIST UPDATED!!!!! with {addr[0]}')
                            self.attenders_list.append(addr[0])
    
    def _whocanserveme(self):
        while True:
            if self.ip and self.mask:
                Thread(
                    target=Send_Broadcast_Message,
                    args=(
                        {'WHOCANSERVEME': ''},
                        Get_Broadcast_Ip(self.ip, self.mask),
                        PLATAFORM_PORT,
                    ),
                    daemon=True,
                ).start()
            sleep(4)
        pass


if __name__ == "__main__":
    # server = ThreadedServer(AgentService(), port=12345)
    # server.start()

    # How to access to a method in remote service
    # a = c.root.__getattr__('iter_find_value')(1)

    print(AgentService._get_exposed_info(AgentService))
    # MyService.__dict__['exposed_sum'])

