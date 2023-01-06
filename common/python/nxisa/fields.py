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

from .base import Field

class OpCode(Field):
    """
    Operation identifier field for each instruction. Normally 3-bits wide, but
    shortened to 2-bits wide for SHUFFLE.
    """

    def __init__(self, op : str = "MEMORY") -> None:
        super().__init__("op", 3, {
                            "MEMORY"     : 0,
                            "WAIT"       : 1,
                            "TRUTH"      : 2,
                            "PICK"       : 3,
                            "RESERVED4"  : 4,
                            "RESERVED5"  : 5,
                            "SHUFFLE"    : 6,
                            "SHUFFLE_ALT": 7,
                        })
        self.op_name  = op.upper()
        self.op_value = self.values[self.op_name]
        if self.op_name == "SHUFFLE":
            self.width = 2

    def match(self, value : int) -> bool:
        return self.extract(value) == self.op_value


class Slot(Field):
    """ Selects between the upper or lower 8-bit slot in the memory row """

    def __init__(self) -> None:
        super().__init__("slot",
                         2, {
                            "PRESERVE": 0,
                            "INVERSE" : 1,
                            "LOWER"   : 2,
                            "UPPER"   : 3,
                         })


class Address_10_7(Field):
    """ Upper 4-bits of the memory address field"""

    def __init__(self) -> None:
        super().__init__("address_10_7", 4)


class Address_6_0(Field):
    """ Lower 7-bits of the memory address field """

    def __init__(self) -> None:
        super().__init__("address_6_0", 7)


class Mux(Field):
    """ Bit selection mux control from an 8-bit value """

    def __init__(self, name) -> None:
        super().__init__(name, 3, group="mux")


class Register(Field):
    """ Working register selection """

    def __init__(self, name : str, group : str = None) -> None:
        super().__init__(name, 3, group=group)


class Source(Register):
    """ Source working register selection """

    def __init__(self, name):
        super().__init__(name, group="src")


class Target(Register):
    """ Target working register selection """

    def __init__(self):
        super().__init__("tgt")


class SendRow(Field):
    """ Row number of the target node to send to """

    def __init__(self) -> None:
        super().__init__("send_row", 4)


class SendColumn(Field):
    """ Column number of the target node to send to """

    def __init__(self) -> None:
        super().__init__("send_col", 4)


class MemoryMode(Field):
    """ Selects between memory instruction modes """

    def __init__(self) -> None:
        super().__init__("mode",
                         2, {
                            "LOAD"     : 0,
                            "STORE"    : 1,
                            "SEND"     : 2,
                            "RESERVED3": 3,
                         })


class Mask(Field):
    """ 4-bit wide bit masking """

    def __init__(self) -> None:
        super().__init__("mask", 4)


class Control(Field):
    """ Base control field type """


class Flag(Control):
    """ Generic 1-bit wide flag field type """

    def __init__(self, name : str) -> None:
        super().__init__(name, 1)


class Table(Field):
    """ Encoded 3 input truth table (8-bit wide) """

    def __init__(self) -> None:
        super().__init__("table", 8)
