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

from .base import Reserved
from .fields import (OpCode, Address_10_7, Address_6_0, Slot, MemoryMode,
                     Source, Target, SendRow, SendColumn, Mux, Mask, Flag,
                     Table)
from .instrdef import InstructionDef


class MemoryDef(InstructionDef):
    """ Perform load/store to local memory, or send to a remote node's memory """

    def __init__(self) -> None:
        super().__init__(OpCode("MEMORY"),
                         Source("src_a"),
                         SendColumn(),
                         SendRow(),
                         Address_10_7(),
                         Target(),
                         MemoryMode(),
                         Address_6_0(),
                         Slot())


class WaitDef(InstructionDef):
    """ Stall execution and wait for the next trigger pulse """

    def __init__(self) -> None:
        super().__init__(OpCode("WAIT"),
                         Reserved(27),
                         Flag("idle"),
                         Flag("pc0"))


class TruthDef(InstructionDef):
    """ Evaluate a 3 input truth table """

    def __init__(self) -> None:
        super().__init__(OpCode("TRUTH"),
                         Source("src_a"),
                         Mux("mux_0"),
                         Mux("mux_1"),
                         Mux("mux_2"),
                         Source("src_b"),
                         Reserved(3),
                         Source("src_c"),
                         Table())


class PickDef(InstructionDef):
    """ Pick 3 bits from a register and store to a (short) memory address """

    def __init__(self) -> None:
        super().__init__(OpCode("PICK"),
                         Source("src_a"),
                         Mux("mux_0"),
                         Mux("mux_1"),
                         Mux("mux_2"),
                         Mux("mux_3"),
                         Mask(),
                         Flag("upper"),
                         Address_6_0(),
                         Slot())


class ShuffleDef(InstructionDef):
    """ Rearrange the 8 bits of a register into an arbitrary order """

    def __init__(self) -> None:
        super().__init__(OpCode("SHUFFLE"),
                         Source("src_a"),
                         Mux("mux_0"),
                         Mux("mux_1"),
                         Mux("mux_2"),
                         Mux("mux_3"),
                         Target(),
                         Mux("mux_4"),
                         Mux("mux_5"),
                         Mux("mux_6"),
                         Mux("mux_7"))
        # Forceably move opcode from 30->29 as bit 29 is overloaded by a mux
        self.opcode.lsb = 29
