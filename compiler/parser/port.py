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

from .signal import Signal

class PortDirection(IntEnum):
    INPUT  = 0
    OUTPUT = 1
    INOUT  = 2

class Port(Signal):
    """ Representation of a port on a module """

    def __init__(self, name, direction, parent, width, bits):
        """ Initialise the Port instance.

        Args:
            name     : Name of the port
            direction: Direction of the port
            parent   : The parent cell or module
            width    : Width of the signal
            bits     : List of bit IDs that this signal carries
        """
        super().__init__(name, width, bits)
        assert direction in PortDirection
        from .cell import Cell
        from .module import Module
        assert type(parent) in (Cell, Module)
        self.direction = direction
        self.parent    = parent

    @property
    def is_input(self): return self.direction == PortDirection.INPUT
    @property
    def is_output(self): return self.direction == PortDirection.OUTPUT
    @property
    def is_inout(self): return self.direction == PortDirection.INOUT

    @property
    def drivers(self):
        from .cell import Cell
        from .constant import Constant
        from .module import Module
        mod = self.parent if isinstance(self.parent, Module) else self.parent.parent
        return [
            (x if isinstance(x, Constant) else mod.get_bit_driver(x))
            for x in self.bits
        ]

    @property
    def targets(self):
        from .cell import Cell
        from .constant import Constant
        from .module import Module
        mod = self.parent if isinstance(self.parent, Module) else self.parent.parent
        return [
            (x if isinstance(x, Constant) else mod.get_bit_targets(x))
            for x in self.bits
        ]
