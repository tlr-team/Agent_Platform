import rpyc
from inspect import isfunction, getfullargspec
from rpyc.utils.server import ThreadedServer
from threading import Thread, Lock
from engine.utils.logger import setup_logger
from engine.utils.network import Udp_Message, Send_Broadcast_Message, Get_Broadcast_Ip
from socket import socket, SO_REUSEADDR, SOL_SOCKET, SOCK_DGRAM

setup_logger(name='AgentService')


def get_funcargs(func):
    args = getfullargspec(func).args
    return args[1:] if 'self' == args[0] else args


class AgentService(rpyc.Service):
    def __init__(self, ip , mask, port):
        self.ip = ip
        self.mask = mask
        self.port = port
        self.attenders_list = []
        self.attenders_list_lock = Lock()
        Thread(target=self._whocanserveme, daemon=True).start()
        Thread(target=self._refresh_attenders,daemon=True).start()
        Thread(target=self._publish_service,daemon=True).start()
        
    def exposed_sum(self, a, b):
        ''' Suma dos enteros y retorna la suma. '''
        return a + b

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
            if len(self.attenders_list):
                sleep(10)
            else:
                sleep(2)


if __name__ == "__main__":
    # server = ThreadedServer(AgentService(), port=12345)
    # server.start()

    # How to access to a method in remote service
    # a = c.root.__getattr__('iter_find_value')(1)

    print(AgentService._get_exposed_info(AgentService))
    # MyService.__dict__['exposed_sum'])

