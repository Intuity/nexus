# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

from dataclasses import dataclass

from cocotb.utils import get_sim_time

@dataclass
class AXI4StreamTransaction:
    """ A single transaction to send """
    data    : bytearray
    id      : int = 0
    dest    : int = 0
    user    : int = 0
    wakeup  : int = 0
    created : int = 0

    def __post_init__(self):
        self.created = int(get_sim_time(units="ns"))

    def pack(self, size=4):
        """ Pack carried data into chunks of a specified size

        Args:
            size: Number of bytes per chunk

        Returns: Zipped list of packed bytes, and list of strobe values
        """
        source = self.data[:]
        packed = []
        strobe = []
        while source:
            chunk  = source[:size]
            source = source[size:]
            packed.append(sum([y << (x * 8) for x, y in enumerate(chunk)]))
            strobe.append(sum([1 << x for x in range(len(chunk))]))
        return zip(packed, strobe)
