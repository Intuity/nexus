# Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
