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

from typing import Any, Dict, List, Tuple, Union, Optional

from .base import Field, Reserved
from .fields import OpCode

class InstructionDef:
    """ Defines the full encoding of an instruction """

    ALL = {}

    def __init__(self, opcode : OpCode, *fields : List[Field]) -> None:
        self.opcode = opcode
        # Group fields together
        self.all_fields = list(fields)
        self.fields     = {}
        lsb             = 0
        for field in self.all_fields:
            # Assign LSB & MSB
            field.lsb = lsb
            lsb       = field.msb + 1
            # Categorise
            if field.group in self.fields:
                if not isinstance(self.fields[field.group], list):
                    self.fields[field.group] = [self.fields[field.group]]
                self.fields[field.group].append(field)
            else:
                self.fields[field.group] = field
        self.__dict__.update(self.fields)
        self.opcode.lsb = lsb
        # Sanity check
        assert (bw := sum((x.width for x in [self.opcode] + self.all_fields))) == 32, (
            f"Fields sum to {bw} bits"
        )
        # Register
        InstructionDef.ALL[type(self).__name__] = self

    def display(self):
        parts = [self.opcode.op_name]
        for field in self.all_fields[::-1]:
            parts.append(f"{field.name.upper()}[{field.msb}:{field.lsb}]")
        return parts

    def __call__(self, comment : str = "", **fields : Dict[str, Any]) -> "Instance":
        return Instance(self, comment=comment, **fields)

    def encode(self, fields : Dict[str, Union[int, List[int]]]) -> int:
        """ Encode fields of an operation into an integer value """
        encoded = self.opcode.op_value << self.opcode.lsb
        for key, value in fields.items():
            if isinstance(value, list):
                for field, entry in zip(self.fields[key], value):
                    encoded |= (entry & field.mask) << field.lsb
            else:
                encoded |= (value & self.fields[key].mask) << self.fields[key].lsb
        return encoded

    @classmethod
    def decode(cls, value : int) -> Tuple["InstructionDef", Dict[str, Union[int, List[int]]]]:
        """ Decode an integer value into an instruction and field definitions """
        # Work out which instruction encoding is used
        for idef in cls.ALL.values():
            if idef.opcode.match(value):
                break
        else:
            raise Exception(f"No instruction matched for 0x{value:08X}")
        # Unpack fields
        decoded = {}
        for key, field in idef.fields.items():
            if isinstance(field, list):
                decoded[key] = []
                for sub in field:
                    decoded[key].append(sub.extract(value))
            else:
                decoded[key] = field.extract(value)
        return idef, decoded

    def to_asm(self, fields : Dict[str, Union[int, List[int]]]) -> str:
        """ Write fields out as an assembly string """
        unpacked = []
        for key, field in self.fields.items():
            if isinstance(field, Reserved) or (isinstance(field, list) and isinstance(field[0], Reserved)):
                continue
            if isinstance(field, list):
                chunk = list(map(field[0].to_asm, fields.get(key, [])))
                unpacked += chunk + ([field[0].to_asm(0)] * (len(field) - len(chunk)))
            else:
                unpacked.append(field.to_asm(fields[key]))
        return f"{self.opcode.op_name.upper():7s} " + ", ".join(list(map(str, unpacked)))

    @classmethod
    def from_asm(cls, asm : str) -> Tuple["InstructionDef", Dict[str, Union[int, List[int]]]]:
        """ Decode an assembly string into an instruction and field definitions """
        op_str, other = asm[:asm.index(" ")], asm[asm.index(" ")+1:]
        parts         = [x.strip() for x in other.split(",")]
        # Work out which instruction encoding is used
        for idef in cls.ALL.values():
            if idef.opcode.op_name.upper() == op_str.upper():
                break
        else:
            raise Exception(f"No instruction matched for {op_str}")
        # Unpack fields
        decoded = {}
        for key, field in idef.fields.items():
            if isinstance(field, Reserved) or (isinstance(field, list) and isinstance(field[0], Reserved)):
                continue
            if isinstance(field, list):
                raw, parts   = parts[:len(field)], parts[len(field):]
                decoded[key] = list(map(field[0].from_asm, raw))
            else:
                decoded[key] = field.from_asm(parts.pop(0))
            if not parts:
                break
        return idef, decoded


class Instance:
    """ Holds an instance of an instruction (definition and field values) """

    def __init__(self, instr : InstructionDef, comment : str = "", **fields) -> None:
        self.instr   = instr
        self.comment = comment
        self.fields  = fields
        # Check fields against the instruction definition
        for key, value in self.fields.items():
            if key not in instr.fields:
                raise Exception(f"Unknown field '{key}'")
            elif isinstance(instr.fields[key], list) != isinstance(value, list):
                exp = type(instr.fields[key]).__name__
                got = type(value).__name__
                raise Exception(f"Mismatching field type for '{key}' expected: {exp}, got: {got}")
            # Apply value encoding to the instruction
            if isinstance(value, list):
                self.fields[key] = list(map(instr.fields[key].encode, value))
            else:
                self.fields[key] = instr.fields[key].encode(value)

    def __repr__(self) -> str:
        return f"<nxisa::{self.instr.opcode.op_name:7s}: {self.fields}>"

    def encode(self) -> int:
        """ Encode the instance fields using the instruction definition """
        return self.instr.encode(self.fields)

    def to_asm(self, address : Optional[int] = None) -> str:
        """
        Write out the instance fields as an assembly string using the instruction
        definition
        """
        base = self.instr.to_asm(self.fields)
        if address is not None or self.comment:
            base += " " * max(40 - len(base), 0)
            base += " //"
        if address is not None:
            base += f" @ 0x{address:03X}"
        if self.comment:
            base += f" {self.comment}"
        return base
