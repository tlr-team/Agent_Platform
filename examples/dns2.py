from dns import DNS_SEARCHER

a = DNS_SEARCHER('10.6.98.230',24, False)
print(a.Get_Service_List())
print(a.DNS_Query('www.cubadebate.cu'))