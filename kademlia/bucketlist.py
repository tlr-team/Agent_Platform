from .kbucket import KBucket, K
from .dht import Id
from .contact import Contact
from threading import Lock


class BucketList:
    '''
    Manages the contacts (peers) in each bucket and the algorithm 
    for adding contacts (peers) to a particular bucket.
    '''

    def __init__(self, _id: Id, k=K):
        self.__our_id = _id
        self.__buckets = [
            KBucket(low=2 ** i, high=2 ** (i + 1) - 1, k=k) for i in range(160)
        ]

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
        contact.touch()

        with self.buckets_lock:
            kbucket = self.getbucket(contact.id)

            # If return false -> the bucket is full
            if kbucket.add_contact(contact):
                return True  # No need to ping
            return (
                False
            )  # Need to refresh bucket (Do Pings and remove disconnected ones)

    # def contains(self, key :Id):
    #     return self.buckets

    def getbucket(self, key: Id):
        return [b for b in self.buckets if b.hasinrange(key)][0]

    def getbucket_ind(self, key: Id):
        return [i for i in range(len(self.buckets)) if self.buckets[i].hasinrange(key)][
            0
        ]

