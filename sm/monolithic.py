import socket as sock
from datetime import datetime, timedelta
from utils.logger import getLogger
from utils.network import Encode_Request, Decode_Response


class ServicesManager:
    def __init__(self, port, forgery_time=30000):
        self.services = {}
        self.forgery_time = timedelta(microseconds=forgery_time)
        self.port = port
        self.logger = getLogger()

        self.sock = sock.socket(type=sock.SOCK_STREAM)
        self.sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, True)
        self.sock.bind(('', self.port))
        self.sock.listen(1024)

    def add_agent(self, service, agent):
        if service in self.services:
            self.services[service][0].append(agent)
            self.services[service] = (self.services[service][0], datetime.now())
        else:
            self.services[service] = ([agent], datetime.now())

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
            client, _ = self.sock.accept()
            msg = Decode_Response(client.recv(2048))

            if 'get' in msg:
                if msg['get'] == 'list':
                    self.get_list_h(msg, client)
                else:
                    self.get_agents_h(msg, client)
                self.logger.info(f'petition: {msg}')
            elif 'post' in msg:
                self.post_service_h(msg, client)
                self.logger.info(f'petition: {msg}')
            else:
                self.logger.error(f'malformed petition: {msg}')
            client.close()

    def get_list_h(self, msg, c_sock):
        '''
        Handler request that send an agent list from a given service.
        '''
        c_sock.send(Encode_Request(list(self.services.keys())))

    def get_agents_h(self, msg, c_sock):
        '''
        Handler request that send an agent list from a given service.  
        '''
        c_sock.send(Encode_Request(list(self.get_agents(msg['get']))))

    def post_service_h(self, msg, c_sock):
        '''
        Handler request that recieve and store an agent info in the given service.  
        '''
        self.add_agent(
            msg['post'], (msg['ip'], msg['port'], msg['url'], msg['protocol'])
        )


if __name__ == "__main__":
    sm = ServicesManager(9342)
    sm()
