ID_LENGTH_BYTES = 20


class Dht:
    '''
    The peer's entry point for interacting whit others peers.
    '''

    def __init__(self, router):
        self.__router = router

    @property
    def router(self):
        return self.__router
