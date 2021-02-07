from .base import Base

class Signal(Base):
    """ Representation of a signal within the design """

    def __init__(self, name, width, bits):
        """ Initialise the Signal instance.

        Args:
            name : Name of the signal
            width: Width of the signal
            bits : List of bit IDs that this signal carries
        """
        super().__init__(name)
        assert isinstance(width, int ) and width > 0
        assert isinstance(bits,  list) and len(bits) >= 0
        from .constant import Constant
        assert len([x for x in bits if type(x) not in (int, Constant)]) == 0
        self.width      = width
        self.bits       = bits
