from ..utils.network import Tcp_Message
from ..utils.logger import getLogger
from threading import Thread, Lock
from random import randint

class SimpleDataBase:
    def __init__(self, logger=getLogger()):
        '''
        Clase que mantiene un funcionamiento Basico de una Bd de agentes (Thread Safe)
        '''
        self.dbs = {}
        self.lock = Lock()
        self.dblogger = logger

    def _insert(self, tag, agent):
        '''
        Inserta un nuevo agente y si existe, acutaliza su tiempo de vida
        '''
        with self.lock:
            if not tag in self.dbs:
                self.dbs[tag] = [(agent,6)]
            else:
                if not agent in self.dbs[tag]:
                    self.dbs[tag].append((agent,6))
                else:
                    for i in self.dbs[tag]:
                        if agent in i:
                            self.dbs[tag][i] = (agent,6)

    def _get(self,tag):
        '''
        Devuelve una lista con a lo sumo 3 agentes que tienen ese servicio
        '''
        with self.lock:
            n_data = len(self.dbs[tag])
            response = []
            if n_data:
                if n_data <= 3:
                    for i in range(0,n_data):
                        self.dblogger.debug(f'i:{i}, self.dbs[i]:{self.dbs[i]} self.dbs[i][0]:{self.dbs[i][0]}')
                        response.append(self.dbs[i][0])
                else:
                    a = randint(0,n_data-1)
                    b = randint(0,n_data-1)
                    while(b == a):
                        b = randint(0,n_data-1)
                    c = randint(0,n_data-1)
                    while(c == a or c == b):
                        c = randint(0,n_data-1)
                    choice = [a,b,c]
                    for i in choice:
                        response.append(self.dbs[tag][i][0])
            return response

    def _reset(self):
        '''
        Reinicia la BD
        '''
        self.dbs = {}

