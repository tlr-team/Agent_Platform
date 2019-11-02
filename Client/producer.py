from producer_options import Log_Path,Error_Path,Service_Port,Server_Port,Server_Ip
from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR,SOCK_STREAM
from json import dumps, loads

server = (Server_Ip,Server_Port)
producers = []

Resource = "A"

local = socket(type = SOCK_STREAM)
local.setsockopt(SOL_SOCKET, SO_REUSEADDR, True)
local.bind(('localhost', Service_Port))
local.listen(100)

while True:
    client, addr = local.accept()
    cp = socket(type = SOCK_STREAM)
    msg = client.recv(1024)
    print(msg)
    cp.connect(server)
    cp.send(msg)
    msgcp = cp.recv(1)
    while(msgcp != b''):
        client.send(msgcp)
        print(msgcp)
        msgcp = cp.recv(1)
    cp.close()
    client.close()


# def Get_Data(s):
#     msg, addr = s.recvfrom(2048)
#     producers = loads(msg)


# def Connect_To_Cp(Cpip,cpport):
