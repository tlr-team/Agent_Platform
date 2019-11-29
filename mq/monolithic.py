import socket as sock
from time import sleep
from threading import Thread, Lock
from utils.logger import getLogger
from utils.network import Decode_Response, Encode_Request


class MessaggeQueue:
    def __init__(self, port_reciever, port_reader):
        self.p_reciever, self.p_reader = port_reciever, port_reader
        self.lock_q = Lock()
        self.queue = []
        self.logger = getLogger()

    def __call__(self, forever=False, time=3600):
        self.s_reciever = sock.socket(type=sock.SOCK_DGRAM)
        self.s_reciever.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, True)
        self.s_reciever.bind(('', self.p_reciever))

        self.s_reader = sock.socket(type=sock.SOCK_DGRAM)
        self.s_reader.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, True)
        self.s_reader.bind(('', self.p_reader))

        self.logger.info(f'clients port:{self.p_reciever}, router port:{self.p_reader}')

        Thread(target=self._recieve, daemon=True, name='reciever').start()
        Thread(target=self._read, daemon=True, name='read').start()

        while True:
            sleep(10)

    # hilo que se encarga de procesar los pedidos de los clientes
    def _recieve(self):
        while True:
            self.logger.info('ready for clients...')
            rawmsg, addr = self.s_reciever.recvfrom(2048)
            msg = Decode_Response(rawmsg)
            self.logger.info(f'arrive: {msg}, from: {addr}')

            if 'get' in msg:
                msg.update({'ip': addr[0], 'port': addr[1]})

            with self.lock_q:
                self.queue.insert(0, msg)

    # Hilo que se encarga de procesar los pedidos hacia los routers
    def _read(self):
        while True:
            self.logger.info('ready for router...')
            rawmsg, addr = self.s_reader.recvfrom(2048)
            msg = Decode_Response(rawmsg)
            if msg != 'get':
                self.logger.error(f'wierd petition from addr {addr}.')
                continue
            self.logger.info(f'request from router: {msg}')

            with self.lock_q:
                self.logger.info(f'queue.size() -> {self.queue}')
                msg = self.queue.pop() if self.queue else {}
                if len(msg):
                    self.logger.info(f'sended to router: {msg}')
                    self.s_reader.sendto(Encode_Request(msg), addr)


def main_test():
    mq = MessaggeQueue(10001, 10002)
    mq()


if __name__ == "__main__":
    main_test()

