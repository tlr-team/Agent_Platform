from time import monotonic
from collections import OrderedDict
from .contact import Contact
from threading import Lock


class KBucket:
    '''
    Retains the collection of contacts (peers) that are associated whit a specific bucket, 
    implements the bucket split algorithm and provides methods for obtaining 
    information regarding the bucket.
    '''

    def __init__(self, low, high, k):
        '''
        (ksize = k)
        (low <= [*ids] <= high)
        '''
        self.ksize = k
        self.contacts_dict = OrderedDict()
        self.low, self.high = low, high
        self.lock = Lock()

    @property
    def contacts(self):
        return list(self.contacts_dict.values())

    @property
    def bucket_is_full(self):
        return len(self.contacts_dict) <= self.ksize

    def hasinrange(self, id):
        assert isinstance(id, int)
        return self.low <= id <= self.high

    def add_contact(self, contact: Contact):
        self.remove_contact(contact)
        if len(self.contacts_dict) < self.ksize:
            self.contacts_dict[contact.id] = contact
            return True
        else:
            # bucket full
            return False

    def remove_contact(self, contact: Contact):
        if contact in self.contacts_dict:
            del self.contacts_dict[contact.id]
            return True
        return False

    def __contains__(self, o):
        if isinstance(o, Contact) and o.id in self.contacts_dict:
            return True
        if isinstance(o, int) and o in self.contacts_dict:
            return True
        return False

    def __len__(self):
        return len(self.contacts_dict)

    def __iter__(self):
        return iter(self.contacts_dict.values())

    def __bool__(self):
        return len(self) != 0

    def __str__(self):
        return f'<[{self.low},{self.high}],len={len(self)}>'

    __repr__ = __str__

