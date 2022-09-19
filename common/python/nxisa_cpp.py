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

import sys

import nxisa

# Extract field positions
fields = {}
for instr in nxisa.InstructionDef.ALL.values():
    for field in [instr.opcode] + instr.all_fields:
        if isinstance(field, nxisa.Reserved):
            continue
        lsb, msb = fields.get(field.name, (None, None))
        if lsb is None or field.lsb < lsb:
            lsb = field.lsb
        if msb is None or field.msb > msb:
            msb = field.msb
        fields[field.name] = (lsb, msb)

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    fh.write("#ifndef __NXISA_HPP__\n")
    fh.write("#define __NXISA_HPP__\n")
    fh.write("\n")
    fh.write("namespace NXISA {\n")
    fh.write("\n")
    fh.write("    // Operation encoding\n")
    fh.write("    typedef enum {\n")
    for idx, (key, val) in enumerate(nxisa.OpCode().values.items()):
        fh.write(f"        {',' if idx else ' '} OP_{key.upper()} = {val}\n")
    fh.write("    } opcode_t;\n")
    fh.write("\n")
    fh.write("    // Offset encoding\n")
    fh.write("    typedef enum {\n")
    for idx, (key, val) in enumerate(nxisa.Offset().values.items()):
        fh.write(f"        {',' if idx else ' '} OFFSET_{key.upper()} = {val}\n")
    fh.write("    } offset_t;\n")
    fh.write("\n")
    fh.write("    // Field positions\n")
    for key, (lsb, msb) in fields.items():
        fh.write(f"    unsigned int {key.upper()}_LSB   = {lsb};\n")
        fh.write(f"    unsigned int {key.upper()}_MSB   = {msb};\n")
        fh.write(f"    unsigned int {key.upper()}_WIDTH = {msb-lsb+1};\n")
        fh.write(f"    unsigned int {key.upper()}_MASK  = (1 << {key.upper()}_WIDTH) - 1;\n")
    fh.write("\n")
    fh.write("    // Field extraction functions\n")
    for key in fields.keys():
        fh.write(f"    uint32_t extract_{key.lower()} ( uint32_t raw ) {'{'} ")
        fh.write(f"return (raw >> {key.upper()}_LSB) & {key.upper()}_MASK;")
        fh.write( " }\n")
    fh.write("\n")
    fh.write("}\n")
    fh.write("\n")
    fh.write("#endif // __NXISA_HPP__\n")