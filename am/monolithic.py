import socket as sock
from json import dumps, loads
from datetime import datetime, timedelta


class AgentManager:
    def __init__(self, port, forgery_time=30000):
        self.agents = {}
        self.forgery_time = timedelta(microseconds=forgery_time)
        self.port = port

        self.sock = sock.socket(type=sock.SOCK_STREAM)
        self.sock.setsockopt(sock.SOL_SOCKET, sock.SO_REUSEADDR, True)
        self.sock.bind(('localhost', 9347))
        self.sock.listen(1024)

    def add_agent(self, key, value):
        self.agents[key] = (value, datetime.now())

    def remove_forgotten(self):
        now = datetime.now()
        for ag in self.agents:
            if now - self.agents[ag][1] >= self.forgery_time:
                del self.agents[ag]

    def get_service(self, agent):
        if self.agents.get(agent):
            return self.agents[agent][1]
        return None

    def get_all_agents(self):
        return self.agents

    def __call__(self):
        while True:
            client, _ = self.sock.accept()
            msg = loads(client.recv(2048))  # FIXME: byte a byte

            if 'get' in msg:
                if msg['get'] == 'full_list':
                    self.get_full_list_h(msg, client)
                if msg['get'] == 'resource':
                    self.get_service_h(msg, client)
            elif 'post' in msg:
                self.post_service_h(msg, client)
            else:
                print('malformed pakage: ', msg)
            client.close()

    def post_service_h(self, msg, c_sock):
        '''
        Handler request that recieve and store an agent-service info.  
        '''
        if 'key' in msg and 'value' in msg:
            self.add_agent(msg['key'], msg['value'])
            print('pakage: ', msg)
        else:
            print('malformed pakage: ', msg)

    def get_full_list_h(self, msg, c_sock):
        '''
        Handler request that send the full list of agents.  
        '''
        c_sock.send(dumps({'value': self.get_all_agents()}).encode())
        print('pakage: ', msg)

    def get_service_h(self, msg, c_sock):
        '''
        Handler request that send a service for a given agent.  
        '''
        if 'key' in msg:
            c_sock.send(
                dumps(
                    {'key': msg['key'], 'value': self.get_service(msg['key'])}
                ).encode()
            )
            print('pakage: ', msg)
        else:
            print('malformed pakage: ', msg)


if __name__ == "__main__":
    am = AgentManager(9343)
    am()
