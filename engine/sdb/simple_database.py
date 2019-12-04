from ..utils.network import Tcp_Message
from threading import Thread, Lock
from random import randint

class SimpleDataBase:
    def __init__(self):
        '''
        Clase que mantiene un funcionamiento Basico de una Bd de agentes (Thread Safe)
        '''
        self.dbs = {}
        self.lock = Lock()

    def _insert(self, tag, agent):
        '''
        Inserta un nuevo agente y si existe, acutaliza su tiempo de vida
        '''
        with self.lock:
            if not tag in self.dbs:
                self.dbs[tag] = [(agent,6)]
            else:
                if not agent in self.dbs[tag]:
                    self.dbs[tag].append(agent,6)
                else:
                    self.dbs[tag][1] = 6

    def _get(self,tag):
        '''
        Devuelve una lista con a lo sumo 3 agentes que tienen ese servicio
        '''
        with self.lock:
            n_data = len(self.dbs.keys()) 
            response = []
            if n_data:
                if n_data <= 3:
                    for i in range(0,n_data):
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

    def _reset(self):
        '''
        Reinicia la BD
        '''
        self.dbs = {}

