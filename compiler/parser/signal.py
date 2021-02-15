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

from .base import Base
from .bit import Bit

class Signal(Base):
    """ Representation of a signal within the design """

    def __init__(self, name, width):
        """ Initialise the Signal instance.

        Args:
            name : Name of the signal
            width: Width of the signal
        """
        super().__init__(name)
        assert isinstance(width, int) and width > 0
        self.bits = [Bit(x, self) for x in range(width)]

    @property
    def width(self): return len(self.bits)

    def __getitem__(self, key):
        return self.bits[key]
