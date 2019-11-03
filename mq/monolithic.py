import socket as sock
from time import sleep
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
        print(f'socket for recieve messages:{self.p_reciever}\nsocket for get messages:{self.p_reader}')
        
        Thread(target=self._recieve, daemon=True).start()
        Thread(target=self._read, daemon=True).start()
        
        while True:
            sleep(5)
            pass

    def _recieve(self):
        while True:
            print('ready for reciever...')
            rawmsg, addr = self.s_reciever.recvfrom(2048)
            msg = loads(rawmsg)
            print('arrive:', msg,'from:', addr)
            
            if msg['type'] == 'consummer':
                msg.update({'ip': addr[0], 'port': addr[1]})

            self.sem.acquire()
            print('\n'.join(str(m) for m in self.queue))
            self.queue.insert(0, msg)
            self.sem.release()
        

    def _read(self):
        while True:
            print('ready for reader...')
            rawmsg, addr = self.s_reader.recvfrom(128)
            msg = loads(rawmsg)
            if msg != 'get':
                print(f'wierd petition from addr {addr}.')
                continue
            print('request recieved from reader:', msg)

            self.sem.acquire()
            msg = self.queue.pop() if self.queue else {}
            print(self.queue)
            self.sem.release()
            self.s_reader.sendto(dumps(msg).encode(), addr)

def main_test():
    mq = MessaggeQueue(8081, 8082)
    mq()

if __name__ == "__main__":
    main_test()
    