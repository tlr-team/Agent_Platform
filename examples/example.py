import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client.agent import AgentService
from time import sleep

class example(AgentService):
    def __init__(self, ip='10.6.98.230', mask=25, port=12345):
        super(example,self).__init__(ip,mask,port)

    def exposed_example(self):
        '''
        This is an example mehtod, nothing to recive, nothing to do
        '''

a = example()

while(True):
    sleep(10)