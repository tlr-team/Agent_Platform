import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.agent import AgentService

class substractor(AgentService):
    def __init__(self, ip, mask, port):
        super(substractor,self).__init__(ip, mask, port)


    def exposed_substrac(self, a, b):
        '''
        This mehtod returns the substracion of two numbers a and b
        '''
        return a - b