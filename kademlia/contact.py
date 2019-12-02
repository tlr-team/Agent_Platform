from time import monotonic
from hashlib import sha1
from .dht import Id


class Contact:
    '''
    Mantains the info that the contact (peers), 
    wich is used for determinig whether a peer should be tested for eviction.
    '''

    def __init__(self, addr, contact_id=None):
        self.last_seen = None
        # self.protocol = protocol
        self.addr = addr
        self.id = Id(
            contact_id or sha1((':'.join((addr[0], str(addr[1])))).encode()).hexdigest()
        )  # contact_id must be and bytelike, intlike or strhexlike

    @property
    def to_dict(self):
        return {'addr': self.addr, 'id': self.id}

    @staticmethod
    def from_dict(_dict,):
        return Contact(_dict['addr'], int(_dict['id']) ^ _dict['our_id'].value)

    def touch(self):
        self.last_seen = monotonic()
