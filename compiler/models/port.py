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

class PortDirection(IntEnum):
    INPUT  = 0
    OUTPUT = 1
    INOUT  = 2

class Port:
    """ Represents a port on a module or operation """

    def __init__(self, name, direction, width, parent):
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
        self.width     = width
        self.inbound   = None # Signal or concatenation driving this port
        self.outbound  = []   # All signals or slices driven by this port
        self.parent    = parent

    @property
    def is_input(self): return (self.direction == PortDirection.INPUT)
    @property
    def is_output(self): return (self.direction == PortDirection.OUTPUT)
    @property
    def is_inout(self): return (self.direction == PortDirection.INOUT)
