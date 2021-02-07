class Base:
    """ Base model """

    def __init__(self, name):
        """ Initialise the Base instance.

        Args:
            name: Name of the model
        """
        assert isinstance(name, str)
        self.name       = name
        self.attributes = {}

    @property
    def safe_name(self):
        return self.name.translate(str.maketrans({
            "[" : "_", "]" : "_", ":" : "_", "\\": "_",
        }))

    def set_attribute(self, key, value):
        """ Add an arbitrary attribute to the signal.

        Args:
            key  : Key of the attribute (must be a string)
            value: Value of the attribute (any type)
        """
        assert isinstance(key, str)
        self.attributes[key] = value
