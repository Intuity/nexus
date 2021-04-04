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

class BitVector:
    """ Class for manipulating packed bit fields """

    def __init__(self, raw, width):
        """ Initialise with the raw value and a width.

        Args:
            raw  : The raw vector
            width: The width of the vector
        """
        assert isinstance(raw,   int)
        assert isinstance(width, int) and width > 1
        self.raw   = raw
        self.width = width

    def extract(self, lsb, width):
        """ Extract a field from the vector.

        Args:
            lsb  : LSB of the field to extract
            width: Width of the field to extract

        Returns: Integer value of the extracted field
        """
        assert lsb >= 0 and lsb < self.width
        assert width > 0 and (lsb + width - 1) < self.width
        return ((self.raw >> lsb) & ((1 << width) - 1))

    def insert(self, lsb, width, value):
        """ Insert a field into the vector.

        Args:
            lsb  : LSB of the field to insert
            width: Width of the field to insert
            value: Value to place
        """
        self.raw &= (((1 << self.width) - 1) - (((1 << width) - 1) << lsb))
        self.raw |= (value & ((1 << width) - 1)) << lsb

    def __getitem__(self, sel):
        if isinstance(sel, slice):
            assert sel.step == None
            msb = max(sel.start, sel.stop)
            lsb = min(sel.start, sel.stop)
            return self.extract(lsb, (msb - lsb) + 1)
        elif isinstance(sel, int):
            return self.extract(sel, 1)
        else:
            return super().__getitem__(sel)

    def __setitem__(self, sel, val):
        if isinstance(sel, slice):
            assert sel.step == None
            msb = max(sel.start, sel.stop)
            lsb = min(sel.start, sel.stop)
            return self.insert(lsb, (msb - lsb) + 1, val)
        elif isinstance(sel, int):
            return self.insert(sel, 1, val)
        else:
            return super().__getitem__(sel)
