'''
Leader Db File
'''

from ..utils.leader_election import Leader_Election, StoppableThread

class DbLeader():
    def __init__(self, ip, port):
