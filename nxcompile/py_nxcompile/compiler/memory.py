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

from typing import Any, List, Optional, Tuple


class MemoryConstants:
    """ Sizing constants for the memory """
    BITS_PER_SLOT : int = 8
    SLOTS_PER_ROW : int = 2
    TOTAL_ROWS    : int = 2048


class MemorySlot:
    """ An 8-bit element of the memory """

    def __init__(self, row : "MemoryRow", index : int):
        self.row        = row
        self.index      = index
        self.__elements = [None] * MemoryConstants.BITS_PER_SLOT

    @property
    def empty(self):
        return all((x is None) for x in self.__elements)

    def __getitem__(self, key : int) -> Any:
        return self.__elements[key]

    def __setitem__(self, key : int, value : Any) -> None:
        assert self.__elements[key] is None, f"Overriding element {key}"
        self.__elements[key] = value
        # Track first location where a signal is placed
        if value is not None and value.name not in self.row.memory.mapping:
            self.row.memory.mapping[value.name] = (self.row.index, self.index, key)

    @property
    def elements(self) -> List[Any]:
        return self.__elements[:]


class MemoryRow:
    """ A 16-bit row within the memory (holds 2 x 8-bit slots) """

    def __init__(self, memory : "Memory", index : int):
        self.memory  = memory
        self.index   = index
        self.__slots = [MemorySlot(self, x) for x in range(MemoryConstants.SLOTS_PER_ROW)]

    @property
    def slots(self) -> List[MemorySlot]:
        return self.__slots[:]

    def __getitem__(self, key : int) -> MemorySlot:
        return self.__slots[key]


class Memory:
    """ Full memory, lazily populated """

    def __init__(self):
        self.__rows    = [MemoryRow(self, 0)]
        self.last_row  = 0
        self.last_slot = 0
        self.mapping   = {}

    def __getitem__(self, key : int) -> Any:
        return self.__rows[key]

    @property
    def rows(self) -> List[MemoryRow]:
        return self.__rows[:]

    @property
    def row(self):
        return self[self.last_row]

    @property
    def slot(self):
        return self[self.last_row][self.last_slot]

    @property
    def slot_pair_lower(self):
        return self[self.last_row][0]

    @property
    def slot_pair_upper(self):
        return self[self.last_row][1]

    def add_row(self) -> MemoryRow:
        if len(self.__rows) >= MemoryConstants.TOTAL_ROWS:
            raise Exception(f"Exhausted the memory ({MemoryConstants.TOTAL_ROWS})")
        self.last_row  += 1
        self.last_slot  = 0
        self.__rows.append(row := MemoryRow(self, self.last_row))
        return row

    def align(self) -> None:
        if self.last_slot == 0 and self.slot_pair_lower.empty and self.slot_pair_upper.empty:
            return
        self.add_row()

    def bump_slot(self) -> None:
        self.last_slot += 1
        if self.last_slot >= MemoryConstants.SLOTS_PER_ROW:
            self.add_row()

    def find(self,
             signal : Any,
             default : Optional[Tuple[int, int, int]]=None) -> Tuple[int, int, int]:
        """
        Locate a particular signal within the memory, returns a tuple of the row,
        slot, and bit index where the signal is stored.
        """
        return self.mapping.get(signal.name, default)
