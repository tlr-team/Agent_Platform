from time import monotonic
from collections import OrderedDict
from .contact import Contact
from .dht import Id

K = 3  # FIXME: Put a correct value


class KBucket:
    '''
    Retains the collection of contacts (peers) that are associated whit a specific bucket, 
    implements the bucket split algorithm and provides methods for obtaining 
    information regarding the bucket.
    '''

    def __init__(self, low=0, high=2 ** 160, k=K):
        self.timestamp = None
        self.ksize = k
        self.contacts = OrderedDict()
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
            self.contacts
        if len(self.contacts) == self.ksize:
            raise Exception('Too many contacts.')  # TODO: Customize Error
        self.contacts[contact.Id] = contact

    def __contains__(self, o):
        if isinstance(o, Contact) and o.id in self.contacts:
            return True
        if isinstance(o, Id) and o in self.contacts:
            return True
        return False
