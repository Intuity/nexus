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

from itertools import groupby
from operator import itemgetter

from .signal import Signal
from .bit import Bit

class Select:
    """ Represents a bit selection from a signal """

    def __init__(self, signal, *bits):
        """ Initialise the Select instance.

        Args:
            signal: Signal instance to select from
            bits  : List of bits to select (or a range)
        """
        assert isinstance(signal, Signal)
        assert len(bits) > 0
        self.signal = signal
        self.bits   = []
        # Built the list of bits if a range was given, else copy the list
        if len(bits) == 1 and isinstance(bits[0], range):
            self.bits += [x for x in bits[0]]
        else:
            assert len([x for x in bits if not isinstance(x, int)]) == 0
            self.bits = [x for x in bits]
        # Sort the bits in ascending order
        self.bits.sort()

    def __repr__(self):
        parts = []
        for lsb, msb in self.groups():
            if lsb == msb:
                parts.append(f"{self.signal.name}[{lsb}]")
            else:
                parts.append(f"{self.signal.name}[{lsb}:{msb}]")
        return "{ " + ", ".join(parts) + " }"

    def groups(self):
        """ Groups selected bits into continuous sequences.

        Returns: List of tuples - tuple contains lowest and highest bit index
        """
        groups = []
        for k, g in groupby(enumerate(sorted(self.bits)), lambda x: x[0] - x[1]):
            group = list(map(int, map(itemgetter(1), g)))
            groups.append((min(group), max(group)))
        return sorted(groups, key=lambda x: x[0])
