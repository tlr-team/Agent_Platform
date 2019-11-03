# Servidor de la plataforma de agentes de pruebas para responder las peticiones de los clientes consumidores

from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
from json import dumps

s = socket(type = SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
s.bind(('', 10001))

while True:
    msg, addr = s.recvfrom(1024)
    print(msg, "from", addr)
    response = [{ "IP":"192.168.2.7", "Port":8000, "Service":"Discover", "Protocol":"TCP" }]
    s.sendto(dumps(response),addr)