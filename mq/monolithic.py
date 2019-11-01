import socket as sock
from json import loads, dumps
from threading import Thread, Semaphore

class MessaggeQueue:
    def __init__(self, port_reciever, port_reader):
        self.p_reciever, self.p_reader = port_reciever, port_reader
        self.sem = Semaphore()
        self.queue = []
        
    def __call__(self, forever = False, time=3600):
        self.s_reciever = sock.socket(type=sock.SOCK_DGRAM)
        self.s_reciever.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, True)
        self.s_reciever.bind(('localhost', self.p_reciever)) #FIXME: Cambiar puerto

        self.s_reader = sock.socket(type=sock.SOCK_DGRAM)
        self.s_reader.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, True)
        self.s_reader.bind(('localhost', self.p_reader)) #FIXME: Cambiar puerto
        
        threads = [
            Thread(target=self._recieve).run(),
            Thread(target=self._read).run(),
        ]
        while True:
            pass
        # for t in threads:
        #     t.join()
        
    def _recieve(self):
        while True:
            rawmsg, addr = self.s_reciever.recvfrom(2048)
            msg = loads(rawmsg)
            if msg['type'] == 'consummer':
                msg.update({'ip': addr[0], 'port': addr[1]})

            self.sem.acquire()
            print(self.queue)
            self.queue.insert(0, msg)
            self.sem.release()
        

    def _read(self):
        while True:
            rawmsg, addr = self.s_reader.recvfrom(128)
            msg = loads(rawmsg)
            if msg != 'get':
                print(f'Wierd petition from addr {addr}.')
                return

            self.sem.acquire()
            msg = self.queue.pop()
            print(self.queue)
            self.sem.release()
            self.s_reader.sendto(dumps(msg), addr)

def main_test():
    mq = MessaggeQueue(8081, 8082)
    mq()

if __name__ == "__main__":
    main_test()
    