from .signal import Signal

class Constant(Signal):
    """ Represents a constant value """

    def __init__(self, value, width):
        """ Initialise the Constant instance.

        Args:
            value: The value of the constant (as an integer)
            width: Width of the constant
        """
        assert isinstance(value, int)
        super().__init__(f"{value:0{width}b}", width, [])
        self.value = value
