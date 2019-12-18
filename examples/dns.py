import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.Client.agent import PlatformInterface
from time import sleep
from sol import *

a = PlatformInterface('10.6.98.230',mask=24)
lista = a.get_service_list()
a.register_agent('10.6.100.66',53,'',1,"DNS")
print(lista)
i = 0
while(True):
    print(a.get_service_list())
    sleep(4)
    i+=1
    if i > 1:
        break

target = a.get_agent('DNS' ,timeout=10)
print(target)

if target:
    response = do_query('www.google.com', QT_A, target['ip'], target['port'])

print(response)