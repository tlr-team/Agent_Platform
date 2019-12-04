from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
from time import sleep
from threading import Thread, Lock
from utils.logger import getLogger
from utils.network import Decode_Response, Encode_Request, Discovering
from utils.leader_election import Leader_Election


class MessageHandler(Leader_Election):
    def __init__(self, port_reciever, port_reader):
        self.p_reciever, self.p_reader = port_reciever, port_reader
        self.lock_q = Lock()
        self.queue = []
        self.logger = getLogger()
        self.logger.info(f'clients port:{self.p_reciever}, router port:{self.p_reader}')
        Thread(target=self._client_serve, daemon=True, name='client_server').start()
        Thread(target=self._router_serve, daemon=True, name='router_server').start()
        while True:
            sleep(10)

    # region Client
    def _client_serve(self):
        self.logger.info('ready for clients...')
        with socket(type = SOCK_DGRAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            sock.bind(('', self.p_reciever))
            sock.listen()

            while(True):
                rawmsg, addr = self.s_reciever.recvfrom(2048)
                Thread(target=self._recieve, args=(rawmsg, addr), daemon = True).start()
    # endregion

    def _router_serve(self):
        self.logger.info('ready for routers...')
        with socket(type = SOCK_DGRAM) as sock:
            sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
            sock.bind(('', self.p_reader))
            sock.listen()

            while(True):
                rawmsg, addr = self.s_reciever.recvfrom(2048)
                Thread(target=self._read, args=(rawmsg, addr), daemon = True).start()



    # hilo que se encarga de procesar los pedidos de los clientes
    def _recieve(self, rawmsg, addr):
        msg = Decode_Response(rawmsg)
        self.logger.info(f'arrive: {msg}, from: {addr}')

        if 'get' in msg:
            msg.update({'ip': addr[0], 'port': addr[1]})

        with self.lock_q:
            self.queue.insert(0, msg)

    # Hilo que se encarga de procesar los pedidos hacia los routers
    def _read(self, rawmsg, addr):
        msg = Decode_Response(rawmsg)
        if msg != 'get':
            self.logger.error(f'wierd petition from addr {addr}.')
            exit()
        self.logger.info(f'request from router: {msg}')

        with self.lock_q:
            self.logger.info(f'queue.size() -> {self.queue}')
            msg = self.queue.pop() if self.queue else {}
            if len(msg):
                self.logger.info(f'sended to router: {msg}')
                self.s_reader.sendto(Encode_Request(msg), addr)
