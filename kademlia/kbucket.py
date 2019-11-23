from datetime import datetime

K = 20  # FIXME: Put a correct value


class KBucket:
    '''
    Retains the collection of contacts (peers) that are associated whit a specific bucket, 
    implements the bucket split algorithm and provides methods for obtaining 
    information regarding the bucket.
    '''

    def __init__(self, low=0, high=2 ** 160):
        self.timestamp: datetime = None
        self.__contacts = []
        self.low, self.high = low, high

    @property
    def contacts(self):
        return self.__contacts

    @property
    def bucket_is_full(self):
        return len(self.contacts) == K

    def touch(self):
        self.timestamp = datetime.now()

    def add_contact(self, contact):
        if len(self.contacts) == K:
            raise Exception('Too many contacts.')  # TODO: Customize Error
        self.contacts.append(contact)
