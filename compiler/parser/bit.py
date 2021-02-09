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

from .signal import Signal

class Bit(Signal):
    """ Represents a single bit """

    def __init__(self, id):
        """ Initialise the Bit instance.

        Args:
            id: Bit ID from Yosys
        """
        super().__init__(f"bit_{id}", 1, [self])
        self.id      = id
        self.signals = []

    def link(self, signal):
        """ Link the bit to a signal """
        assert isinstance(signal, Signal)
        self.signals.append(signal)
