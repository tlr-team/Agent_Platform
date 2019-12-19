from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
from time import sleep
from threading import Thread, Lock
from ..utils.logger import getLogger
from ..utils.network import Decode_Response, Encode_Request, Udp_Message
from ..utils.leader_election import Leader_Election


class MessageHandler:
    def __init__(self, logger = getLogger(), client_port=10000, message_router_port=10001, discovering_port=10003):
        self.client_port , self.router_port, self.discovering_port = client_port, message_router_port, discovering_port
        self.lock_q = Lock()
        self.queue = []
        self.logger = logger
        self.logger.info(f'clients port:{self.client_port}, router port:{self.router_port}')

    def start(self):
        Thread(target=self._server, args=(True,), daemon=True).start()
        t = Thread(target=self._server, args=(False,))
        t.start()
        t.join()

    def _server(self, client = True):
        self.logger.info('ready for clients...' if client else 'ready for routers...')
        with socket(type = SOCK_DGRAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            sock.bind(('', self.client_port if client else self.router_port))

            while(True):
                rawmsg, addr = sock.recvfrom(2048)
                Thread(target=self._recieve if client else self._read, args=(rawmsg, addr), daemon = True).start()


    # hilo que se encarga de procesar los pedidos de los clientes
    def _recieve(self, rawmsg, addr):
        msg = Decode_Response(rawmsg)
        self.logger.info(f'arrive: {msg}, from: {addr}')

        if 'get' in msg or 'post' in msg:
            if 'get' in msg or 'info' in msg:
                msg.update({'client_ip': addr[0], 'client_port': addr[1]})

            with self.lock_q:
                self.queue.insert(0, msg)
        
        elif 'WHOCANSERVEME' in msg:
            Udp_Message({'ME':''}, addr[0], 10004)


    # Hilo que se encarga de procesar los pedidos hacia los routers
    def _read(self, rawmsg, addr):
        msg = Decode_Response(rawmsg)
        self.logger.info(f'request {msg} from router: {addr}')
        if 'get' in msg:
            with self.lock_q:
                self.logger.info(f'queue.size() -> {self.queue}')
                msg = self.queue.pop() if self.queue else {}
            if len(msg):
                Udp_Message(msg, *addr)
                self.logger.info(f'sended {msg} to router: {addr}')
                
        elif 'WHOCANSERVEME' in msg:
            Udp_Message({'ME':'MQ'}, addr[0], 10003)
            print('UDPDATE SENT')
