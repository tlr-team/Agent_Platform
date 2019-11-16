from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from json import dumps, loads
from .network import Get_Subnet_Host_Number,Send_Broadcast_Message,Decode_Response,Encode_Request

class Leader_Election:
    # primero llegua y pregunta quien es el leader ,si recibe un "" convoca a elecciones
    # si el leader que recibe no esta, convoca a elecciones

    # el lider
    # cuando es elegido, realiza un broadcast con su id
    # cuando recibe un pedido de elecciones, este deja de ser lider

    # 
    pass