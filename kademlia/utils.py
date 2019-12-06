from rpyc import VoidService, SocketStream, connect_stream
from time import monotonic
from threading import Lock, Thread, Semaphore
from engine.utils.logger import getLogger


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


class Node:
    def __init__(self, value, tree_constant):
        self.id = value.id
        self.value = value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return self.value != other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value


class SortedQueue:
    def __init__(self, k, main_id):
        self.k = k
        self.queue = []
        self.mid = main_id

    def __add(self, nde: Node):
        for i in range(0, len(self.queue)):
            if nde < self.queue[i]:
                self.queue.insert(i, nde)
        if len(self.queue) > self.k:
            self.queue.pop()

    def add(self, _id):
        self.add(Node(_id, self.mid))

    def getall(self):
        return [i.value for i in self.queue]


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
