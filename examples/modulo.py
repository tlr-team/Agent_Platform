import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.agent import AgentService


class Modulo(AgentService):
    def __init__(self, ip, port, mask):
        super(Modulo, self).__init__(ip, port, mask)

    def exposed_mod(self, a, b):
        '''
            Returns the rest of the division from one number to another number b
        '''
        if a < 0 or b <= 0:
            return -1
        elif a < b:
            return a
        else:
            remainder = a
            while remainder > b:
                remainder = self.execute('Substractor', 'subtract', remainder, b)
            return remainder


if __name__ == "__main__":
    Modulo.start('10.6.98.243', 24, 12345)
