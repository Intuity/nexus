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

from .gate import Gate

class PortDirection(IntEnum):
    INPUT  = 0
    OUTPUT = 1
    INOUT  = 2

class PortBit:
    """ Represents a bit within a port """

    def __init__(self, port, index):
        """ Initialise the PortBit instance.

        Args:
            port : The parent port
            index: Bit index within the port
        """
        assert isinstance(port, Port) or port == None
        assert isinstance(index, int)
        self.port      = port
        self.index     = index
        self.__driver  = None  # What drives this bit
        self.__targets = []    # What is driven by this bit

    @property
    def driver(self):
        return self.__driver

    @driver.setter
    def driver(self, drv):
        if self.__driver: raise Exception("Driver has already been set")
        assert isinstance(drv, PortBit) or isinstance(drv, Gate)
        self.__driver = drv

    def clear_driver(self):
        """ Clear the held driver """
        self.__driver = None

    @property
    def targets(self):
        return self.__targets[:]

    def add_target(self, tgt):
        assert isinstance(tgt, PortBit) or isinstance(tgt, Gate)
        self.__targets.append(tgt)

    def remove_target(self, tgt):
        assert isinstance(tgt, PortBit) or isinstance(tgt, Gate)
        assert tgt in self.__targets
        self.__targets.remove(tgt)

    def clear_targets(self):
        """ Clear any held targets """
        self.__targets = []

class Port:
    """ Represents a port on a module or operation """

    def __init__(self, name, direction, width, parent=None):
        """ Initialise the Port instance.

        Args:
            name     : Name of the port
            direction: Direction of the port
            width    : Bit width of the port
            parent   : Pointer to the parent Module
        """
        assert isinstance(name, str)
        assert direction in PortDirection
        assert isinstance(width, int) and width > 0
        self.name      = name
        self.direction = direction
        self.bits      = [PortBit(self, x) for x in range(width)]
        self.parent    = parent

    def __repr__(self):
        return (
            f"<Port (0x{id(self):X}) N: {self.name}, W: {self.width}, D: "
            f"{self.direction}, P: {type(self.parent).__name__}::{self.parent.name}>"
        )

    @property
    def is_input(self): return (self.direction == PortDirection.INPUT)
    @property
    def is_output(self): return (self.direction == PortDirection.OUTPUT)
    @property
    def is_inout(self): return (self.direction == PortDirection.INOUT)

    @property
    def width(self): return len(self.bits)

    @property
    def drivers(self):
        return set([x.driver for x in self.bits])

    @property
    def targets(self):
        return set([
            (y.port if isinstance(y, PortBit) else y)
            for x in self.bits for y in x.targets
        ])

    def __getitem__(self, key):
        return self.bits[key]
