from datetime import datetime


class Contact:
    '''
    Mantains the protocol that the contact (peers) uses, 
    wich is used for determinig whether a peer should be tested for eviction.
    '''

    def __init__(self, protocol, contact_id):
        self.last_seen: datetime = None
        self.protocol = protocol
        self.id = contact_id
        self.touch()

    def touch(self):
        self.last_seen = datetime.now()
