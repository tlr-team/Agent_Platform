from engine.Client.cmd_client import Client

a = Client(ip='10.6.98.230', mask=24, port=10000)
a.cmdloop()