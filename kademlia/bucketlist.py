from .kbucket import KBucket
from .contact import Contact
from threading import Lock
from engine.utils.logger import getLogger
from .utils import to_str
from engine.utils.logger import setup_logger, debug, error, info
from json import dump


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
        # lock for syncronous use of the bucketlist
        self.buckets_lock = Lock()

    @property
    def buckets(self):
        return self.__buckets

    @property
    def id(self):
        return self.__our_id

    def add_contact(self, contact: Contact):
        debug(f'[bucketlist] Adding contact: {contact}.')
        contact.touch()
        # with self.buckets_lock:
        bucket = self.get_bucket(contact.id)
        bucket.lock.acquire()
        result = bucket.add_contact(contact)  # false -> the bucket is full
        bucket.lock.release()
        debug(
            f'[bucketlist] Contact:{contact}' + f' added to bucket {bucket}.'
            if result
            else f' bucket {bucket} is full.'
        )
        with open('log/bucket_list.log', 'w') as f:
            dump([str(i) for i in self.buckets if i], f, indent=True)
        return result

    def get_bucket(self, key):
        debug(f'[bucketlist] key:{key}.')
        with self.buckets_lock:
            i = self.get_bucket_ind(key)
            bucket = self.buckets[i]
        debug(f'[bucketlist] Index:{i} Bucket:{bucket}.')
        return bucket

    def get_bucket_ind(self, key):
        debug(f'[bucketlist] key:{key}.')
        distance = key ^ self.id
        debug(f'[bucketlist] Distance:{distance} = key:{key} ^ id:{self.id}.')
        i = [
            i
            for i in range(self.b)
            if self.buckets[i].hasinrange(distance + 1 if not distance else distance)
        ].pop()
        debug(f'[bucketlist] Index:{i}, str(distance)={to_str(distance)}.')
        return i

    def _get_all_bucket_contacts(self, bucketlist, index) -> iter:
        for contact in bucketlist[index]:
            yield contact

    def get_closest(self, key) -> list:
        with self.buckets_lock:
            index = self.get_bucket_ind(key)
        debug(f'[bucketlist] id:{key}, (id)bucket-index:{index}')

        left_bucks = self.buckets[:index]
        center = self.buckets[index]
        right_bucks = self.buckets[index + 1 :]
        res = []

        with center.lock:
            for contact in center:
                res.append(contact)
            debug(f'[bucketlist] Sended {len(res)} from the center bucket')
        li = len(left_bucks) - 1
        ri = 0
        while li >= 0 and ri < len(right_bucks):
            with left_bucks[li].lock:
                res.extend(self._get_all_bucket_contacts(left_bucks, li))
            if len(left_bucks[li]):
                debug(
                    f'[bucketlist] Sended {len(left_bucks[li])} until the {li}th bucket.'
                )
            with right_bucks[ri].lock:
                res.extend(self._get_all_bucket_contacts(right_bucks, ri))
            if len(right_bucks[ri]):
                debug(
                    f'[bucketlist] Sended {len(right_bucks[ri])} until the {index + ri + 1}th bucket.'
                )
            li -= 1
            ri += 1

        while li >= 0:
            with left_bucks[li].lock:
                res.extend(self._get_all_bucket_contacts(left_bucks, li))
            if len(left_bucks[li]):
                debug(
                    f'[bucketlist] Sended {len(left_bucks[li])} until the {li}th bucket.'
                )
            li -= 1
        while ri < len(right_bucks):
            with right_bucks[ri].lock:
                res.extend(self._get_all_bucket_contacts(right_bucks, ri))
            if len(right_bucks[ri]):
                debug(
                    f'[bucketlist] Sended {len(right_bucks[ri])} until the {index + ri + 1}th bucket.'
                )
            ri += 1
        return res

    def __getitem__(self, i: int):
        assert i < self.k and i >= 0
        res = None
        with self.buckets_lock:
            res = self.buckets[i]
        return res
