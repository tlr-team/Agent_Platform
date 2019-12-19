import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.agent import AgentService


class Substractor(AgentService):
    def __init__(self, ip, mask, port):
        super(Substractor, self).__init__(ip, mask, port)

    def exposed_subtract(self, a, b):
        '''
        Returns the subtraction of two numbers a and b
        '''
        return a - b


if __name__ == "__main__":
    Substractor.start('10.6.98.243', 24, 12345)
