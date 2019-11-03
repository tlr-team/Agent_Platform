# Servidor de la plataforma de agentes de pruebas para responder las peticiones de los clientes consumidores

from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
from json import dumps, loads

s = socket(type = SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
s.bind(('', 10001))

while True:
    msg, addr = s.recvfrom(1024)
    print(msg, "from", addr)
    to_do = loads(msg)["get"]
    response = []
    if to_do == "list":
        response = ["cubadebate", "test1", "test2"]
    elif to_do == "cubadebate":
        response = [{ "ip":"192.168.2.7", "port":8000, "service":"discover", "protocol":"tcp" }] 
    s.sendto(dumps(response),addr)