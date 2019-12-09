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
        response = ["cubadebate", "dns", "test2"]
    elif to_do == "cubadebate":
        response = [{ "ip":"190.92.127.78", "port":80, "service":"discover", "stype":"tcp" }]
    elif to_do == "dns":
        response = [{ "ip":"192.168.1.1", "port":53, "service":"dns", "stype":"udp" }] 
    s.sendto(dumps(response).encode("utf-8"),addr)