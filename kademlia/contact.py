from time import monotonic
from hashlib import sha1


class Contact:
    '''
    Mantains the info that the contact (peers), 
    wich is used for determinig whether a peer should be tested for eviction.
    '''

    def __init__(self, addr):
        self.last_seen = None
        # self.protocol = protocol
        self.addr = addr
        self.id = int(sha1((':'.join((addr[0], str(addr[1])))).encode()).hexdigest())

    @property
    def to_dict(self):
        return {'addr': self.addr, 'id': self.id}

    @staticmethod
    def from_dict(_dict,):
        return Contact(_dict['addr'])

    def touch(self):
        self.last_seen = monotonic()
