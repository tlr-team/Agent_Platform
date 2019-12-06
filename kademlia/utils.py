from rpyc import VoidService, SocketStream, connect_stream
from time import monotonic
from threading import Lock, Thread, Semaphore
from engine.utils.logger import getLogger
from time import sleep


def to_str(val: int, endian='little'):
    '''
    `endian`='little' o 'big'
    '''
    byts = ['0' * 8]  # force a positive number
    r = val

    while r != 0:
        if endian is 'little':
            byts.insert(-1, bin(r & 255)[2:].rjust(8, '0'))
        else:
            byts.insert(1, bin(r & 255)[2:].rjust(8, '0'))
        r >>= 8
    return ''.join(byts)


def to_boolean(val: int, endian='little'):
    return [b == '1' for b in to_str(val, endian=endian)]


class KSortedQueue:
    def __init__(self, k, id):
        self.k = k
        self.queue = []
        self.mid = id
        self.lock = Lock()

    def add(self, node):
        self.lock.acquire()
        for i, cur_node in enumerate(self.queue):
            if node.id ^ self.mid < cur_node.id ^ self.mid:
                self.queue.insert(i, node)
                break
        else:
            if len(self.queue) < self.k:
                self.queue.append(node)
        if len(self.queue) > self.k:
            self.queue.pop()
        self.lock.release()

    def __iter__(self):
        self.lock.acquire()
        for node in self.queue:
            yield node.value
        self.lock.release()


def rpyc_connect(
    host, port, service=VoidService, config={}, keepalive=False, timeout=3
):
    '''Creates an rpyc connection.'''
    s = SocketStream.connect(host, port, keepalive=keepalive, timeout=timeout)
    return connect_stream(s, service=VoidService, config=config)


class FakeNTP:
    @staticmethod
    def now():
        '''Gives the monotonic clock time.'''
        return monotonic()
