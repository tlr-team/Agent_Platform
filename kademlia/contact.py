from time import monotonic
from hashlib import sha1
from json import loads, dumps


class Contact:
    '''
    Mantains the info that the contact (peers), 
    wich is used for determinig whether a peer should be tested for eviction.
    '''

    def __init__(self, ip, port, id):
        assert isinstance(port, int) and isinstance(id, int) and isinstance(port, str)
        self.last_seen = None
        self.ip, self.port = ip, port
        self.id = (
            id if id else int(sha1((':'.join((ip, str(port)))).encode()).hexdigest())
        )

    def to_json(self):
        return dumps({'ip': self.ip, 'port': self.port, 'id': self.id})

    @staticmethod
    def from_json(jsn_s):
        _dict = loads(jsn_s)
        return Contact(_dict['ip'], _dict['port'], _dict['id'])

    def __str__(self):
        return f'<{self.id},{self.ip}:{self.port}>'

    __repr__ = __str__

    def __eq__(self, other):
        return self.id == other.id

    def __ne__(self, other):
        return self.id != other.id

    def touch(self):
        self.last_seen = monotonic()
