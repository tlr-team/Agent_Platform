from kademlia.kademlia import (
    DefaultAlfaSize,
    DefaultBSize,
    DefaultKSize,
    KademliaProtocol,
)
from engine.utils.network import get_hash
from kademlia.storage import StorageManager
from engine.utils.logger import setup_logger, debug, error, info
from rpyc.utils.registry import UDPRegistryClient, UDPRegistryServer
from rpyc.utils.server import ThreadedServer
from rpyc import discover, connect
from threading import Thread
from time import sleep
from random import randint
from socket import socket, AF_INET, SOCK_DGRAM, gethostbyname, gethostname
from kademlia.contact import Contact
from engine.utils.network import Decode_Response

setup_logger(name='AgentManager', to_file=True)


class AgentManager(KademliaProtocol):
    '''
        A layer for client's to request info about 
        the agents from the kademlia network. 
    '''

    # region client_interface
    def exposed_get(self, addr):
        ''' 
            Search and return the agent_info (__string__) corresponding
            with the identifier id taken from addr\n
            `id=Hash(addr)`
        '''
        try:
            _addr = Decode_Response(addr)
            _addr = (_addr['ip'], _addr['port'])
            hs = get_hash(addr=_addr)
        except Exception as e:
            error(f'Bad Request:{addr} error: {e}')
            return None
        res = self.exposed_iter_find_value(hs)
        if not res is None:
            return res[0]
        return None

    def exposed_add_agent(self, agent_info, store_time):
        ''' 
            Store the (id, (agent_info, store_time)) in the network.\n
            `id=Hash(agent_info.addr)`
        '''
        debug(f'Processing petition post: {agent_info}')
        agent_info = Decode_Response(agent_info)
        # if not ip in agent_info or not agent_info.get('port'):
        #     error(f'Bad request: {agent_info}')
        #     return False
        hs = get_hash(ip=agent_info['ip'], port=agent_info['port'])
        return self.exposed_iter_store(hs, agent_info, store_time)

    def exposed_all(self):
        ''' Gives all records (most recently ones) '''
        if not self.started:
            error('Node not started.')
            return []
        records = {}

        with self.db_lock:
            for k, vt in self.db.items():
                records[k] = (
                    vt
                    if records.get(k) is None or records[k][1] < vt[1]
                    else records[k]
                )
        return list(records.values())

    def exposed_all_nodes(self):
        ''' Gives all nodes in the node bucket list '''
        pass

    # endregion
    @staticmethod
    def __register_server_starter():
        while True:
            server = None
            try:
                server = UDPRegistryServer()
                debug(f'Starting registration server.')
                server.start()
                break
            except Exception as e:
                debug(f'Registration server not started because {e}')
                sleep(4)

    @staticmethod
    def __service_starter(cls, port: int):
        while True:
            server = None
            try:
                debug('Creating instace of ThreadedServer')
                server = ThreadedServer(
                    cls(),
                    port=port,
                    registrar=UDPRegistryClient(),
                    protocol_config={'allow_public_attrs': True},
                )
                debug('Starting the service')
                server.start()
                break
            except Exception as e:
                error(f'Error starting service Exception: \n{e}\n{e.__traceback__}')
                debug('Sleep a while and retry')
                if not server is None:
                    server.close()
                sleep(0.2)

    @staticmethod
    def get_ip():
        ip = None
        try:
            debug('Discover peers to obtain ip.')
            peers = discover(AgentManager.service_name(AgentManager))
            debug(f'Peers encountred: {peers}')
            if not peers:
                raise Exception('No peer was discovered.')
            for peer in peers:
                s = socket(AF_INET, SOCK_DGRAM)
                try:
                    s.connect(peer)
                    ip = s.getsockname()[0]
                except Exception as e:
                    error(f'Problem whit {peer} Exception:\n{e}')
                s.close()
        except Exception as e:
            error(f'Problem obtaining the ip Exception:\n{e}')
            ip = gethostbyname(gethostname())
        return ip

    @staticmethod
    def start(port=None, port_range=(10000, 10100), first_node=False):
        ''' Connect to the kademlia network, and wait for rpc\'s '''
        print('look in logs ;)...')
        if port is None:
            port = randint(*port_range)
        info(f'Starting on port {port}')
        debug(f'Start tread for start register server.')
        thread_server = Thread(target=AgentManager.__register_server_starter)
        thread_server.start()
        sleep(3)
        debug('Start tread for start service.')
        thread_service = Thread(
            target=AgentManager.__service_starter, args=(AgentManager, port)
        )
        thread_service.start()
        sleep(3)

        ip = AgentManager.get_ip()
        contact = Contact(ip, port)
        assert contact.id == get_hash(
            (ip, port)
        ), f'Calculated hash not correct. -> {contact.id} == {get_hash((ip, port))}'
        while True:
            try:
                debug(
                    f'Trying to connect to service {AgentManager.service_name(AgentManager)}'
                )
                c = connect(ip, port, config={'sync_request_timeout': 1000000})
                res = c.ping()
                debug(f'Ping to ({ip}:{port}) res({res})')
                res = c.root.join_to_network(contact.to_json())
                debug(f'\'join_to_network\' to ({ip}:{port}) res({res})')
                if res:
                    break
                error('connection with himself has crashed')
            except Exception as e:
                error(f'Could\'nt connect to service. Exception:\n{e}')
                debug(f'Sleep a while to retry')
            sleep(1)
        info(f'SERVER STARTED')
