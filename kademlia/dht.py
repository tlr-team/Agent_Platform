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


class Id(int):
    '''
    Helper methods and operators overloads for the XOR logic. 
    '''

    def __init__(self, value):
        self.value = value

    def to_str(self, endian='little'):
        '''
        `endian`='little' o 'big'
        '''
        byts = ['0' * 8]  # force a positive number
        r = self.value

        while r != 0:
            if endian is 'little':
                byts.insert(-1, bin(r & 255)[2:].rjust(8, '0'))
            else:
                byts.insert(1, bin(r & 255)[2:].rjust(8, '0'))
            r >>= 8
        return ''.join(byts)

    def to_boolean(self, endian='little'):
        return [b == '1' for b in self.to_str(endian=endian)]

    @property
    def value(self):
        return self.__intValue

    @value.setter
    def value(self, value):
        if (
            isinstance(value, bytes)
            and (not value.isdigit() or len(value) != ID_LENGTH_BYTES)
            or not isinstance(value, int)
        ):
            raise Exception(
                'value {0} is not in the required format.'.format(value)
            )  # FIXME: Make a custom Exception

        self.__intValue = (
            value
            if isinstance(value, int)
            else abs(int.from_bytes(value, byteorder='little'))
        )  # TODO: Put the correct byte order.

