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

    def __init__(self, name, direction, width, bits):
        """ Initialise the Port instance.

        Args:
            name     : Name of the port
            direction: Direction of the port
            width    : Width of the signal
            bits     : List of bit IDs that this signal carries
        """
        super().__init__(name, width, bits)
        assert direction in PortDirection
        self.direction = direction
        self.inbound   = []
        self.outbound  = []
