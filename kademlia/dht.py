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
        if isinstance(value, bytes) and len(value) != ID_LENGTH_BYTES:
            value = value.hex()
        if isinstance(value, str) and value.isdigit():
            value = int(value, 16)
        if isinstance(value, int):
            self.__intvalue = value
        else:
            raise Exception(
                'value {0} is not in the required format.'.format(value)
            )  # FIXME: Make a custom Exception

    def __xor__(self, other):
        return Id(self.value ^ other.value)

    def __lt__(self, other):
        if isinstance(other, Id):
            return self.value < other.value
        return self.value < other

    def __le__(self, other):
        return self < other or self == other

    def __ge__(self, other):
        return not self < other

    def __gt__(self, other):
        return not self <= other

    def __repr__(self):
        return f'Id({self.value})'

    def __eq__(self, other):
        if isinstance(other, Id):
            return self.value == other.value
        return self.value == other

    def __ne__(self, other):
        return not self == other

    def to_str(self, endian='big'):
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

    def to_boolean(self, endian='big'):
        return [b == '1' for b in self.to_str(endian=endian)]

    @property
    def value(self):
        return self.__intvalue

