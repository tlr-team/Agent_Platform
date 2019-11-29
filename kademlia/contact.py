from datetime import datetime
from hashlib import sha1


class Contact:
    '''
    Mantains the info that the contact (peers), 
    wich is used for determinig whether a peer should be tested for eviction.
    '''

    def __init__(self, addr, contact_id=None):
        self.last_seen: datetime = None
        # self.protocol = protocol
        self.addr = addr
        self.id = contact_id or sha1(':'.join((addr[0], str(addr[1])))).digest()

    @property
    def to_dict(self):
        return {'addr': self.addr, 'id': self.id}

    @staticmethod
    def from_dict(_dict):
        return Contact(_dict['addr'], _dict['id'])

    def touch(self):
        self.last_seen = datetime.now()
