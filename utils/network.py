from socket import socket, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SOCK_STREAM, SO_BROADCAST
from time import sleep
from json import dumps, loads

# decorador que reintenta una función si esta da error cada seconds cantidad de tiempo
def Retry(seconds):
    time_to_sleep = seconds
    def FReciever(function):
        objetive = function
        def wrapper(*args,**kwargs):
            try:
                return objetive(*args,**kwargs)
            except:
                sleep(time_to_sleep)
                return wrapper(*args,**kwargs)
        return wrapper
    return FReciever

# Función que envia un mensaje (en bytes) mediante  broadcast y devuelve el resultado de una función a la que se le pasa el socket
# Esta función no falla dado que siempre va a existir una interfaz a la cual entregar el socket, el manejo de errores se delega en la función a aplicar
def Send_Broadcast_Message(message, function, Broadcast_Address, Broadcast_Port):
    broadcast = socket(type = SOCK_DGRAM)
    broadcast.setsockopt(SOL_SOCKET, SO_BROADCAST, True)
    broadcast.sendto(message, (Broadcast_Address, Broadcast_Port))
    result = function(broadcast)
    broadcast.close()
    return result