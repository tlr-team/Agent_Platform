from time import monotonic
from collections import OrderedDict
from .contact import Contact


class KBucket:
    '''
    Retains the collection of contacts (peers) that are associated whit a specific bucket, 
    implements the bucket split algorithm and provides methods for obtaining 
    information regarding the bucket.
    '''

    def __init__(self, low=1, high=2 ** 160 - 1, k=K):
        '''
        (ksize = k)
        (low <= [*ids] <= high)
        '''
        self.timestamp = None
        self.ksize = k
        self.contacts = OrderedDict()
        self.pending_contacts = OrderedDict()
        self.low, self.high = low, high
        self.touch()

    @property
    def contacts_list(self):
        return list(self.contacts.values())

    @property
    def bucket_is_full(self):
        return len(self.contacts) == self.ksize

    def touch(self):
        self.timestamp = monotonic()

    def hasinrange(self, contact: Contact):
        return self.low <= contact.Id <= self.high

    def add_contact(self, contact: Contact):
        if contact.id in self.contacts:
            del self.contacts[contact.id]
            self.contacts[contact.id] = contact
        elif len(self.contacts) < self.ksize:
            self.contacts[contact.id] = contact
        else:
            if contact.id in self.pending_contacts:
                del self.pending_contacts[contact.id]
            self.pending_contacts[contact.id] = contact
            return False
        return True

    def __contains__(self, o):
        if isinstance(o, Contact) and o.id in self.contacts:
            return True
        if isinstance(o, int) and o in self.contacts:
            return True
        return False
