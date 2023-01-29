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

import sys

import nxisa

# Identify standard field types
fields = {}
for instr in nxisa.instrdef.InstructionDef.ALL.values():
    for field in [instr.opcode] + instr.all_fields:
        if isinstance(field, nxisa.base.Reserved):
            continue
        fields[type(field).__name__] = field

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    fh.write("package NXISA;\n")
    fh.write("\n")
    fh.write("    // Operation encoding\n")
    fh.write(f"    typedef enum logic [{nxisa.fields.OpCode().width-1}:0] {'{'}\n")
    for idx, (key, val) in enumerate(nxisa.fields.OpCode().values.items()):
        fh.write(f"        {',' if idx else ' '} OP_{key.upper()} = 'd{val}\n")
    fh.write("    } f_opcode_t;\n")
    fh.write("\n")
    fh.write("    // Slot encoding\n")
    fh.write(f"    typedef enum logic [{nxisa.fields.Slot().width-1}:0] {'{'}\n")
    for idx, (key, val) in enumerate(nxisa.fields.Slot().values.items()):
        fh.write(f"        {',' if idx else ' '} SLOT_{key.upper()} = 'd{val}\n")
    fh.write("    } f_slot_t;\n")
    fh.write("\n")
    fh.write("    // Memory mode encoding\n")
    fh.write(f"    typedef enum logic [{nxisa.fields.MemoryMode().width-1}:0] {'{'}\n")
    for idx, (key, val) in enumerate(nxisa.fields.MemoryMode().values.items()):
        fh.write(f"        {',' if idx else ' '} MEM_{key.upper()} = 'd{val}\n")
    fh.write("    } f_memorymode_t;\n")
    fh.write("\n")
    fh.write("    // Basic field types\n")
    for name, field in fields.items():
        if not isinstance(field, (nxisa.fields.OpCode,
                                  nxisa.fields.Slot,
                                  nxisa.fields.MemoryMode)):
            if field.width > 1:
                fh.write(f"    typedef logic [{field.width-1}:0] f_{name.lower()}_t;\n")
            else:
                fh.write(f"    typedef logic f_{name.lower()}_t;\n")
    fh.write("\n")
    fh.write("    // Instruction structs\n")
    for name, instr in nxisa.instrdef.InstructionDef.ALL.items():
        fh.write("    typedef struct packed {\n")
        for field in [instr.opcode] + instr.all_fields:
            if isinstance(field, nxisa.base.Reserved):
                fh.write(f"        logic [{field.width-1}:0] {field.name};\n")
            else:
                fh.write(f"        f_{type(field).__name__.lower()}_t {field.name};\n")
        fh.write(f"    {'}'} {name.replace('Def', '').lower()}_t;\n\n")
    fh.write("    // Instruction Union\n")
    fh.write("    typedef union packed {\n")
    for name in nxisa.instrdef.InstructionDef.ALL.keys():
        clean = name.replace("Def", "")
        fh.write(f"        {clean.lower()}_t {clean.lower()};\n")
    fh.write("    } instruction_t;\n")
    fh.write("\n")
    fh.write("endpackage : NXISA\n")
    fh.write("\n")
