import socket as sock
from json import dumps,loads
from datetime import datetime, timedelta


class ServicesManager:
    def __init__(self, port, forgery_time=30000):
        self.services = {}
        self.forgery_time = timedelta(microseconds=forgery_time)
        self.port = port

        self.sock = sock.socket(type=sock.SOCK_DGRAM)
        self.sock.setsockopt(sock.SOCK_STREAM,sock.SO_REUSEADDR,True)
        self.sock.bind(('localhost', self.port))

    def add_agent(self, key, value):
        self.services[key] = (value, datetime.now())
    
    def remove_forgotten(self):
        now = datetime.now()
        for serv in self.services:
            if now - self.services[serv][1] >= self.forgery_time:
                del self.services[serv]

    def get_agents(self, serv):
        if self.services.get(serv):
            return self.services[serv][1]
        return None

    def __call__(self):
        while True:
            rawmsg, addr = self.sock.recvfrom(2048)
            msg = loads(rawmsg)

            if 'key' in msg and 'id' in msg:
                self.sock.sendto(dumps({
                    'id': msg['id'],
                    'key': msg['key'],
                    'value': self.get_agents(msg['key']),
                }), addr)
                print('pakage: ', msg)
            else:
                print('malformed pakage: ', msg)


if __name__ == "__main__":
    sm = ServicesManager(9342)
    sm()
