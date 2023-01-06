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

from typing import Dict, Optional, Union

class Field:

    def __init__(self,
                 name   : str,
                 width  : int,
                 values : Optional[Dict[str, int]] = None,
                 group  : str = None) -> None:
        self.name    = name
        self.width   = width
        self.lsb     = None
        self.values  = values or {}
        self.group   = group or name
        self.mapping = {}
        if self.values:
            self.__dict__.update(self.values)
            self.mapping = { v: k for k, v in self.values.items() }

    @property
    def msb(self):
        return self.lsb + self.width - 1

    @property
    def mask(self):
        """ Generate a bitmask for the field (disregarding LSB) """
        return (1 << self.width) - 1

    def encode(self, value):
        """ Apply encoding mapping to value """
        return self.mapping.get(value, value)

    def decode(self, value):
        """ Apply decoding mapping to value """
        return self.values.get(value, value)

    def extract(self, value : int) -> int:
        """ Extract the value of the field from a fully encoded instruction """
        return (value >> self.lsb) & self.mask

    def to_asm(self, value : Union[str, int]) -> str:
        """ Map an integer to a named value (if one is known) """
        return value if isinstance(value, str) else self.mapping.get(value, value)

    def from_asm(self, value : Union[str, int]) -> int:
        """ Map a named value (if known) or integer back to a integer """
        if isinstance(value, int) or value.isnumeric() or value.startswith("0x"):
            return int(value, 0)
        else:
            return self.values[value.upper()]


class Reserved(Field):

    def __init__(self, width : int) -> None:
        super().__init__("rsvd", width)


class Label:

    def __init__(self, label : str):
        self.__label = label

    def __repr__(self) -> str:
        return f"<nxisa::Label \"{self.label}\">"

    @property
    def label(self):
        return self.__label

    def to_asm(self):
        return f"{self.__label}:"
