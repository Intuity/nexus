from enum import IntEnum

import simpy

class Verbosity(IntEnum):
    ERROR = 0
    WARN  = 1
    INFO  = 2
    DEBUG = 3

class Base:
    """ Base object for simulation """

    VERBOSITY = Verbosity.INFO

    def __init__(self, env, name):
        """ Initialise the Base object.

        Args:
            env : SimPy Environment
            name: Friendly name of the object
        """
        assert isinstance(env,  simpy.Environment)
        assert isinstance(name, str)
        self.env     = env
        self.name    = name
        self.created = self.env.now

    @classmethod
    def set_verbosity(cls, level):
        assert level in Verbosity
        cls.VERBOSITY = level

    # Verbosity filtered logging function
    def __log(self, verb, msg):
        if verb <= Base.VERBOSITY:
            print(f"{self.env.now:08d} [{self.name}] {msg}")

    # Logging aliases
    def error(self, msg): return self.__log(Verbosity.ERROR, msg)
    def warn (self, msg): return self.__log(Verbosity.WARN,  msg)
    def info (self, msg): return self.__log(Verbosity.INFO,  msg)
    def debug(self, msg): return self.__log(Verbosity.DEBUG, msg)
