from .kbucket import KBucket
from .dht import Id


class BucketList:
    '''
    Manages the contacts (peers) in each bucket and the algorithm 
    for adding contacts (peers) to a particular bucket.
    '''

    def __init__(self, _id: Id):
        self.__our_id = _id
        self.__buckets = []
        # first bucket has max range
        self.__buckets.append(KBucket())

    @property
    def buckets(self):
        return self.__buckets

    @property
    def id(self):
        return self.__our_id

    def add_contact(self, contact):
        raise NotImplementedError()
