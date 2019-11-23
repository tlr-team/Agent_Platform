from .dht import Id


class StorageManager:  # TODO: Implements
    '''
    Define operations in dht's Node space assigned and manage consults, downloads and uploads.
    '''

    def __init__(self):
        pass

    def contains(self, key: Id):
        raise NotImplementedError()
        # return boolean

    def try_get_value(self, key: Id):
        raise NotImplementedError()
        # return (boolean,null/str)

    def get(self, key):
        raise NotImplementedError()
        # return str

    def get_timestamp(self, key: Id):
        raise NotImplementedError()
        # return timestamp

    def set(self, key: Id, val: str, expiration_time=0):
        raise NotImplementedError()

    def get_expiration_timesec(self, key):
        raise NotImplementedError()

    def remove(self, key):
        raise NotImplementedError()

    @property
    def keys(self):
        raise NotImplementedError()
        # gemerator of keys stored

    def touch(self, key):
        raise NotImplementedError()

