"""
    Request messages to the MQ.
"""
import socket as sock
from json import dumps, loads
from random import randint
from time import sleep

s = sock.socket(type=sock.SOCK_DGRAM)
s.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, True)
addr = ('localhost', 8082)

request = 'get'

while True:
    s.sendto(dumps(request).encode(), addr)
    print('sended request, waiting for response...')

    rawmsg, addr = s.recvfrom(2048)
    msg = loads(rawmsg)
    print('recieved:', msg)
    sleep(randint(1, 5))
