from .kbucket import KBucket
from .contact import Contact
from threading import Lock
from engine.utils.logger import getLogger
from .utils import to_str


class BucketList:
    '''
    Manages the contacts (peers) in each bucket and the algorithm 
    for adding contacts (peers) to a particular bucket.
    '''

    def __init__(self, _id, k, b):
        self.__our_id = _id
        self.k, self.b = k, b
        self.__buckets = [
            KBucket(low=2 ** i, high=2 ** (i + 1) - 1, k=k)
            for i in range(self.b)  # b = 160
        ]
        self.logger = getLogger(name='BucketList')
        # lock for syncronous use of the bucketlist
        self.buckets_lock = Lock()

    @property
    def buckets(self):
        return self.__buckets

    @property
    def id(self):
        return self.__our_id

    def add_contact(self, contact: Contact):
        self.logger.debug(f'add_contact :: Adding contact:{contact}.')
        contact.touch()
        with self.buckets_lock:
            bucket = self.get_bucket(contact.id)
        bucket.lock.acquire()
        result = bucket.add_contact(contact)  # false -> the bucket is full
        bucket.lock.release()
        self.logger.debug(
            f'add_contact :: contact:{contact}' + f' added to bucket {bucket}.'
            if result
            else f' bucket {bucket} is full.'
        )
        return result

    def get_bucket(self, key):
        self.logger.debug(f'get_bucket :: key:{key}.')
        i = self.get_bucket_ind(key)
        bucket = self.buckets[i]
        self.logger.debug(f'get_bucket :: Index:{i} Bucket:{bucket}.')
        return bucket

    def get_bucket_ind(self, key):
        self.logger.debug(f'get_bucket_ind :: key:{key}.')
        distance = key ^ self.id
        self.logger.debug(
            f'get_bucket_ind :: Distance:{distance} = key:{key} ^ id:{self.id}.'
        )
        i = [i for i in range(self.b) if self.buckets[i].hasinrange(distance)].pop()
        self.logger.debug(
            f'get_bucket_ind :: Index:{i}, str(distance)={to_str(distance)}.'
        )
        return i

    def _get_all_bucket_contacts(self, bucketlist, index) -> iter:
        for contact in bucketlist[index]:
            yield contact

    def get_closest(self, key) -> list:
        self.buckets_lock.acquire()
        index = self.get_bucket_ind(key)
        self.buckets_lock.release()
        self.logger.debug(f'get_closest :: id:{key}, (id)bucket-index:{index}')

        left_bucks = self.buckets[:index]
        center = self.buckets[index]
        right_bucks = self.buckets[index + 1 :]
        res = []

        with center.lock:
            for contact in center:
                res.append(contact)
            self.logger.log(f'get_closest :: Sended {len(res)} from the center bucket')
        li = len(left_bucks) - 1
        ri = 0
        while li >= 0 and ri < len(right_bucks):
            with left_bucks[li].lock:
                res.extend(self._get_all_bucket_contacts(left_bucks, li))
            if len(left_bucks[li]):
                self.logger.log(
                    f'get_closest :: Sended {len(left_bucks[li])} until the {li}th bucket.'
                )
            with right_bucks[ri].lock:
                res.extend(self._get_all_bucket_contacts(right_bucks, ri))
            if len(right_bucks[ri]):
                self.logger.log(
                    f'get_closest :: Sended {len(right_bucks[ri])} until the {index + ri + 1}th bucket.'
                )
            li -= 1
            ri += 1

        while li >= 0:
            with left_bucks[li].lock:
                res.extend(self._get_all_bucket_contacts(left_bucks, li))
            if len(left_bucks[li]):
                self.logger.log(
                    f'get_closest :: Sended {len(left_bucks[li])} until the {li}th bucket.'
                )
            li -= 1
        while ri < len(right_bucks):
            with right_bucks[ri].lock:
                res.extend(self._get_all_bucket_contacts(right_bucks, ri))
            if len(right_bucks[ri]):
                self.logger.log(
                    f'get_closest :: Sended {len(right_bucks[ri])} until the {index + ri + 1}th bucket.'
                )
            ri += 1
        return res
