import logging

log = logging.getLogger("parser.model")

class Model:
    """ Representation of an AIG model from Yosys JSON """

    def __init__(self, name, raw):
        """ Initialise the Model instance.

        Args:
            name: Name of the model
            raw : The raw list from the Yosys JSON output
        """
        assert isinstance(name, str)
        assert isinstance(raw,  list)
        self.name = name
        self.raw  = raw
