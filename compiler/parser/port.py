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

    def __init__(self, name, direction, parent, width):
        """ Initialise the Port instance.

        Args:
            name     : Name of the port
            direction: Direction of the port
            parent   : The parent cell or module
            width    : Width of the signal
        """
        super().__init__(name, width)
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
        return [x.driver.parent for x in self.bits if x.driver]

    @property
    def targets(self):
        return [y.parent for y in sum([x.targets for x in self.bits], [])]
