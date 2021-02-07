from enum import IntEnum

from .signal import Signal

class PortDirection(IntEnum):
    INPUT  = 0
    OUTPUT = 1
    INOUT  = 2

class Port(Signal):
    """ Representation of a port on a module """

    def __init__(self, name, direction, width, bits):
        """ Initialise the Port instance.

        Args:
            name     : Name of the port
            direction: Direction of the port
            width    : Width of the signal
            bits     : List of bit IDs that this signal carries
        """
        super().__init__(name, width, bits)
        assert direction in PortDirection
        self.direction = direction
        self.inbound   = []
        self.outbound  = []
