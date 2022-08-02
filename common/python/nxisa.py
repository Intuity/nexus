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

from typing import Any, Dict, List, Optional, Tuple, Union

from tabulate import tabulate

# NOTE: This implements the NXNode ISA described in `docs/isa.md`

# ==============================================================================
# Field Encodings
# ==============================================================================

class Field:

    def __init__(self, name : str, width : int, values : Optional[Dict[str, int]] = None) -> None:
        self.name    = name
        self.width   = width
        self.lsb     = None
        self.values  = values or {}
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

class OpCode(Field):

    def __init__(self, op : str = "LOAD") -> None:
        super().__init__("op", 3, {
                            "LOAD"       : 0,
                            "STORE"      : 1,
                            "BRANCH"     : 2,
                            "SEND"       : 3,
                            "TRUTH"      : 4,
                            "ARITH"      : 5,
                            "SHUFFLE"    : 6,
                            "SHUFFLE_ALT": 7,
                        })
        self.op_name  = op.upper()
        self.op_value = self.values[self.op_name]
        if self.op_name == "SHUFFLE":
            self.width = 2

    def match(self, value : int) -> bool:
        return self.extract(value) == self.op_value

class Reserved(Field):

    def __init__(self, width : int) -> None:
        super().__init__("rsvd", width)

class Register(Field):

    def __init__(self, name : str) -> None:
        super().__init__(name, 3)

class Immediate(Field):

    def to_asm(self, value: Union[str, int]) -> str:
        """ Always output immediates in hexadecimal (with padding) """
        return f"0x{value:0{(self.width + 3) // 4}X}"

class Control(Field):
    pass

class Source(Register):

    def __init__(self, name):
        super().__init__(name)

class Target(Register):

    def __init__(self):
        super().__init__("tgt")

class Address(Immediate):

    def __init__(self) -> None:
        super().__init__("address", 10)

class PC(Immediate):

    def __init__(self) -> None:
        super().__init__("pc", 10)

class Table(Immediate):

    def __init__(self) -> None:
        super().__init__("table", 8)

class Mask(Immediate):

    def __init__(self) -> None:
        super().__init__("mask", 8)

class Flag(Control):

    def __init__(self, name : str) -> None:
        super().__init__(name, 1)

class Offset(Control):

    def __init__(self) -> None:
        super().__init__("offset",
                         2, {
                            "PRESERVE": 0,
                            "INVERSE" : 1,
                            "SET_LOW" : 2,
                            "SET_HIGH": 3,
                         })

class Comparison(Control):

    def __init__(self) -> None:
        super().__init__("comparison", 3, {
                            "JUMP": 0,
                            "WAIT": 1,
                            "BEQ" : 2,
                            "BNE" : 3,
                            "BGE" : 4,
                            "BLT" : 5,
                            "BEQZ": 6,
                            "BNEZ": 7,
                         })

class ArithOp(Control):
    ADD = 0, "ADD" # 00
    SUB = 1, "SUB" # 01
    AND = 2, "AND" # 10
    OR  = 3, "OR"  # 11

    def __init__(self) -> None:
        super().__init__("func", 2)

class NodeRow(Field):

    def __init__(self) -> None:
        super().__init__("node_row", 4)

class NodeColumn(Field):

    def __init__(self) -> None:
        super().__init__("node_col", 4)

class Mux(Field):

    def __init__(self, name) -> None:
        super().__init__(name, 3)

# ==============================================================================
# Instruction Encodings
# ==============================================================================

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
            if field.name in self.fields:
                if not isinstance(self.fields[field.name], list):
                    self.fields[field.name] = [self.fields[field.name]]
                self.fields[field.name].append(field)
            else:
                self.fields[field.name] = field
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

    def __call__(self, **fields : Dict[str, Any]) -> "Instance":
        return Instance(self, **fields)

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

    def __init__(self, instr : InstructionDef, **fields) -> None:
        self.instr  = instr
        self.fields = fields
        # Check fields against the instruction definition
        for key, value in self.fields.items():
            if key not in instr.fields:
                raise Exception(f"Unknown field '{key}'")
            elif isinstance(instr.fields[key], list) != isinstance(value, list):
                exp = type(instr.fields[key]).__name__
                got = type(instr.fields[key]).__name__
                raise Exception(f"Mismatching field type - expected: {exp}, got: {got}")

    def encode(self) -> int:
        """ Encode the instance fields using the instruction definition """
        return self.instr.encode(self.fields)

    def to_asm(self) -> str:
        """
        Write out the instance fields as an assembly string using the instruction
        definition
        """
        return self.instr.to_asm(self.fields)

class LoadDef(InstructionDef):

    def __init__(self) -> None:
        super().__init__(OpCode("LOAD"),
                         Reserved(3),
                         Target(),
                         Reserved(5),
                         Flag("slot"),
                         Address(),
                         Offset(),
                         Reserved(5))

class StoreDef(InstructionDef):

    def __init__(self) -> None:
        super().__init__(OpCode("STORE"),
                         Source("src_a"),
                         Mask(),
                         Flag("slot"),
                         Address(),
                         Offset(),
                         Reserved(5))

class BranchDef(InstructionDef):

    def __init__(self) -> None:
        super().__init__(OpCode("BRANCH"),
                         Source("src_a"),
                         Reserved(3),
                         Source("src_b"),
                         Reserved(3),
                         PC(),
                         Offset(),
                         Flag("idle"),
                         Comparison(),
                         Flag("mark"))

class SendDef(InstructionDef):

    def __init__(self) -> None:
        super().__init__(OpCode("SEND"),
                         Source("src_a"),
                         NodeColumn(),
                         NodeRow(),
                         Flag("slot"),
                         Address(),
                         Offset(),
                         Flag("Trig"),
                         Reserved(4))

class TruthDef(InstructionDef):

    def __init__(self) -> None:
        super().__init__(OpCode("TRUTH"),
                         Source("src_a"),
                         Target(),
                         Source("src_b"),
                         Source("src_c"),
                         Mux("mux_a"),
                         Mux("mux_b"),
                         Mux("mux_c"),
                         Table())

class ArithmeticDef(InstructionDef):

    def __init__(self) -> None:
        super().__init__(OpCode("ARITH"),
                         Source("src_a"),
                         Target(),
                         Source("src_b"),
                         Reserved(13),
                         ArithOp(),
                         Reserved(5))

class ShuffleDef(InstructionDef):

    def __init__(self) -> None:
        super().__init__(OpCode("SHUFFLE"),
                         Source("src_a"),
                         Target(),
                         Mux("b0"),
                         Mux("b1"),
                         Mux("b2"),
                         Mux("b3"),
                         Mux("b4"),
                         Mux("b5"),
                         Mux("b6"),
                         Mux("b7"))
        # Forceably move opcode from 30->29 as bit 29 is overloaded by a mux
        self.opcode.lsb = 29

# Build instruction encodings
Load       = LoadDef()
Store      = StoreDef()
Branch     = BranchDef()
Send       = SendDef()
Truth      = TruthDef()
Arithmetic = ArithmeticDef()
Shuffle    = ShuffleDef()

# Lint guard
assert all((Load, Store, Branch, Send, Truth, Arithmetic, Shuffle))

# # Check that all encodings present correctly
# all_parts = [x.display() for x in InstructionDef.ALL.values()]
# max_len   = max(len(x) for x in all_parts)
# padded    = [([x[0]] + ([""] * (max_len - len(x))) + x[1:]) for x in all_parts]
# print(tabulate(padded))

# ld     = Load(tgt=3, slot=1, address=127, offset=3)
# ld_enc = ld.encode()
# ld_dec = InstructionDef.decode(ld_enc)
# ld_asm = ld.to_asm()
# ld_prs = InstructionDef.from_asm(ld_asm)
# print(f"LOAD  - ENC: 0x{ld_enc:08X} DEC: {ld_dec} ASM: {ld_asm} PRS: {ld_prs}")

# truth     = Truth(src=[1, 2, 3], tgt=3, imm=57, si=0, table=0xF0)
# truth_enc = truth.encode()
# truth_dec = InstructionDef.decode(truth_enc)
# truth_asm = truth.to_asm()
# truth_prs = InstructionDef.from_asm(truth_asm)
# print(f"TRUTH - ENC: 0x{truth_enc:08X} DEC: {truth_dec} ASM: {truth_asm} PRS: {truth_prs}")
