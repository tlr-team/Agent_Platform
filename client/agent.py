import rpyc
from inspect import isfunction, getfullargspec
from rpyc.utils.server import ThreadedServer
from threading import Thread
from engine.utils.logger import setup_logger

setup_logger(name='AgentService')


def get_funcargs(func):
    return getfullargspec(func).args


class AgentService(rpyc.Service):
    def __init__(self, ip=None, mask=None, port=PORT):
        # Thread(target=self.).start()
        pass

    def exposed_sum(self, a, b):
        ''' Suma dos enteros y retorna la suma. '''
        return a + b

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

    def publish_service(self):
        method_info = AgentService._get_exposed_info(self.__class__)


if __name__ == "__main__":
    # server = ThreadedServer(AgentService(), port=12345)
    # server.start()

    # How to access to a method in remote service
    # a = c.root.__getattr__('iter_find_value')(1)

    print(AgentService._get_exposed_info(AgentService))
    # MyService.__dict__['exposed_sum'])

