from kademlia.kademlia import (
    DefaultAlfaSize,
    DefaultBSize,
    DefaultKSize,
    KademliaProtocol,
)
from kademlia.storage import StorageManager
from engine.utils.logger import setup_logger, debug, error
from rpyc.utils.registry import UDPRegistryClient, UDPRegistryServer
from rpyc.utils.server import ThreadedServer
from time import sleep
from random import randint

setup_logger(name='AgentManager', logfile=__name__.strip('_'))


class AgentManager(KademliaProtocol):
    '''
        A layer for client's to request info about 
        the agents from the kademlia network. 
    '''

    def __init__(self, storage=StorageManager()):
        super(AgentManager, self).__init__(storage)
        debug('[AgentManager] initialized.')
        

    # region client_interface
    def exposed_get(self, addr):
        ''' 
            Search and return the agent_info (__string__) corresponding
            with the identifier id taken from addr\n
            `id=Hash(addr)`
        '''

    def exposed_add_agent(self, agent_info, store_time):
        ''' 
            Store the (id, (agent_info, store_time)) in the network.\n
            `id=Hash(agent_info.addr)`
        '''

    def exposed_all(self):
        ''' Gives all records (most recently ones) '''

    # endregion

    def start(self, port=None, port_range=(10000, 10100)):
        ''' Conect to the kademlia network, and wait for rpc\'s '''
        if port is None:
            port = randint(*port_range)

    @staticmethod
    def __register_server_starter():
        while True:
            server = None
            try:
                debug(f'Starting registration server.')
                server = UDPRegistryServer()
                server.start()
                break
            except Exception as e:
                debug(f'Registration server not started because {e}')
                sleep(4)

    @staticmethod
    def __service_starter(port: int, logger):
        while True:
            server = None
            try:
                debug('Creating instace of service')
                service = AgentManager()
                debug('Creating instace of ThreadedServer')
                server = ThreadedServer(
                    service,
                    port=port,
                    registrar=UDPRegistryClient(),
                    protocol_config={'allow_public_attrs': True},
                )
                debug('Starting the service')
                server.start()
                break
            except Exception as e:
                error(f'Error starting service Exception: \n{e}')
                debug('Sleep a while and retry')
                if not server is None:
                    server.close()
                sleep(0.2)
