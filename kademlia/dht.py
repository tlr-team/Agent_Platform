ID_LENGTH_BYTES = 20


class Dht:
    '''
    The peer's entry point for interacting whit others peers.
    '''


class Id(int):
    '''
    Helper methods and operators overloads for the XOR logic. 
    '''

    def __init__(self, value):
        self.value = value

    @property
    def value(self):
        return self.__intValue

    @value.setter
    def set_value(self, value):
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

