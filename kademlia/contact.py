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
        self.id = contact_id or sha1(':'.join(addr)).digest()

        self.touch()

    def touch(self):
        self.last_seen = datetime.now()
