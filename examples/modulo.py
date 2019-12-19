import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.agent import AgentService

class modulo(AgentService):
    def __init__(self, ip, port, mask):
        super(modulo, self).__init__(ip, port, mask)

    def exposed_mod(self, a, b):
        '''
        Finds the remainder after division of one number a by another number b
        '''
        if a < 0 or b < 0:
            return -1
        elif a < b:
            return a
        else:
            remainder = self.execute('SUBSTRACTOR','substract', a , b)
            while remainder >= b:
                remainder = self.execute('SUBSTRACTOR','substract', remainder , b)
            return remainder
            

                

