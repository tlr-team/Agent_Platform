"""
    Send messages to the MQ.
"""
import socket as sock
from json import dumps, loads
from random import randint
from time import sleep

s = sock.socket(type=sock.SOCK_DGRAM)
s.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, True)
addr = ('localhost', 8081)

petition = {
    'id': 1,
    'type': 'consummer',
    'resource': 'A',
    'fails':[]
}

while True:
    s.sendto(dumps(petition).encode(), addr)
    print('sended petition.')
    sleep(randint(3, 5))

    # rawmsg, addr = s.recvfrom(2048)
    # msg = loads(rawmsg)
    # print('recieved:', msg)
    petition['id'] += 1