from .signal import Signal

class Net(Signal):
    """ Represents a net within the design """

    def __init__(self, name, width, bits, hide=False):
        """ Initialise the Net instance.

        Args:
            name : Name of the net
            width: Width of the signal
            bits : List of bit IDs that this signal carries
            hide : Whether to hide the net's name
        """
        super().__init__(name, width, bits)
        assert isinstance(hide, bool)
        self.hide = hide

    @property
    def safe_name(self):
        return ("__" if self.hide else "") + super().safe_name
