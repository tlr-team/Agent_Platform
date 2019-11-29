from .kbucket import KBucket
from .dht import Id
from .contact import Contact
from threading import Lock


class BucketList:
    '''
    Manages the contacts (peers) in each bucket and the algorithm 
    for adding contacts (peers) to a particular bucket.
    '''

    def __init__(self, _id: Id):
        self.__our_id = _id
        self.__buckets = []

        # lock for syncronous use of the bucketlist
        self.buckets_lock = Lock()

        # first bucket has max range
        self.__buckets.append(KBucket())

    @property
    def buckets(self):
        return self.__buckets

    @property
    def id(self):
        return self.__our_id

    def add_contact(self, contact: Contact):
        assert self.__our_id != contact.Id, 'Cannot add yourself as a Contact'
        contact.touch()

        with self.buckets_lock:
            kbucket = self.getbucket(contact.id)
            if kbucket

    def contains(self, key :Id):
        return self.buckets

    def getbucket(self, key: Id):
        return [i for i in self.buckets if i.id == key].pop()

    def getbucket_ind(self, key: Id):
        return [i for i in range(len(self.buckets)) if self.buckets[i].id == key].pop()

