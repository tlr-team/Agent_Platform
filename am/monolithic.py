import socket as sock
from json import dumps, loads
from datetime import datetime, timedelta


class AgentManager:
    def __init__(self, port, forgery_time=30000):
        self.agents = {}
        self.forgery_time = timedelta(microseconds=forgery_time)
        self.port = port

        self.sock = sock.socket(type=sock.SOCK_DGRAM)
        self.sock.setsockopt(sock.SOCK_STREAM, sock.SO_REUSEADDR, True)
        self.sock.bind(('localhost', self.port))

    def add_agent(self, key, value):
        self.agents[key] = (value, datetime.now())

    def remove_forgotten(self):
        now = datetime.now()
        for ag in self.agents:
            if now - self.agents[ag][1] >= self.forgery_time:
                del self.agents[ag]

    def get_services(self, agent):
        if self.agents.get(agent):
            return self.agents[agent][1]
        return None

    def __call__(self):
        while True:
            rawmsg, addr = self.sock.recvfrom(2048)
            msg = loads(rawmsg)

            if 'key' in msg and 'id' in msg:
                self.sock.sendto(
                    dumps(
                        {
                            'id': msg['id'],
                            'key': msg['key'],
                            'value': self.get_services(msg['key']),
                        }
                    ),
                    addr,
                )
                print('pakage: ', msg)
            else:
                print('malformed pakage: ', msg)


if __name__ == "__main__":
    am = AgentManager(9343)
    am()
