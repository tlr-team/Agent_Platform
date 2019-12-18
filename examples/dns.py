import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.Client.agent import PlatformInterface
from time import sleep
from sol import do_query, QT_A


class DNS_SEARCHER(PlatformInterface):
    def __init__(self, ip, mask):
        super(DNS_SEARCHER, self).__init__(ip, mask)
        self.register_agent('10.6.100.66', 53, '', 1, "DNS")
        self.register_agent('10.6.98.3', 53, '', 1, "DNS")
        # self.delete_agent('8.8.8.8', 53, '', 1, "DNS")
        # self.register_agent('8.8.8.8', 53, '', 1, "DNS")

    def Get_Service_List(self):
        result = self.get_service_list(15)
        while not result:
            print(f'Reintentando')
            result = self.get_service_list(15)
        return result

    def DNS_Query(self, domain):
        target = self.get_agent('DNS', 15)
        while not target:
            print('Reintentando')
            target = self.get_agent('DNS', 15)
        print(target)
        sleep(3)
        return do_query(domain, QT_A, target['ip'], target['port'])


dns = DNS_SEARCHER('10.6.98.230', 24)
print(dns.Get_Service_List())
print(dns.DNS_Query('www.google.com'))
