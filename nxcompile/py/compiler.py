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
from nxcompile import NXParser, NXGate, nxgate_op_t, nxsignal_type_t, nxport_type_t

module = NXParser.parse_from_file(sys.argv[1])

def signame(sig):
    if sig.type == nxsignal_type_t.CONSTANT:
        return "'d" + sig.name
    else:
        return sig.name.replace(".", "_")

with open(sys.argv[2], "w") as fh:
    # Write out the I/O boundary
    fh.write(f"module {module.name} (\n")
    for idx, port in enumerate(module.ports):
        fh.write(f"    {',' if idx else ' '} {port.port_type.name.lower()} logic {signame(port)}\n")
    fh.write(f");\n")
    # Declare all wires
    fh.write(f"\n// Wires\n\n")
    for wire in module.wires:
        fh.write(f"logic {signame(wire)};\n")
    # Declare all flops
    fh.write(f"\n// Flops\n\n")
    for flop in module.flops:
        fh.write(f"logic {signame(flop)};\n")
    # Declare all processes
    fh.write(f"\n// Processes\n\n")
    for idx, flop in enumerate(module.flops):
        if idx > 0: fh.write("\n")
        fh.write(f"always @(posedge {signame(flop.clock)}, posedge {signame(flop.reset)})\n")
        fh.write(f"    if ({signame(flop.reset)}) {signame(flop)} <= {signame(flop.rst_val)};\n")
        fh.write(f"    else {signame(flop)} <= {signame(flop.inputs[0])};\n")
    # Declare all gates
    fh.write(f"\n// Gates and Assignments\n\n")
    for wire in module.wires:
        fh.write(f"assign {signame(wire)} = ")
        if len(wire.inputs) == 0:
            fh.write("'dX")
        elif len(wire.inputs) == 1 and wire.inputs[0].type == nxsignal_type_t.GATE:
            gate = NXGate.from_signal(wire.inputs[0])
            if gate.op == nxgate_op_t.ASSIGN:
                fh.write(signame(gate.inputs[0]))
            elif len(gate.inputs) == 1 and gate.op in (
                nxgate_op_t.AND, nxgate_op_t.OR, nxgate_op_t.NOT, nxgate_op_t.XOR
            ):
                fh.write({
                    nxgate_op_t.AND: "&",
                    nxgate_op_t.OR : "|",
                    nxgate_op_t.NOT: "~",
                    nxgate_op_t.XOR: "^",
                }[gate.op] + "(" + signame(gate.inputs[0]) + ")")
            elif gate.op in (
                nxgate_op_t.AND, nxgate_op_t.OR, nxgate_op_t.NOT, nxgate_op_t.XOR
            ):
                fh.write((" " + {
                    nxgate_op_t.AND: "&",
                    nxgate_op_t.OR : "|",
                    nxgate_op_t.NOT: "~",
                    nxgate_op_t.XOR: "^",
                }[gate.op] + " ").join((signame(x) for x in gate.inputs)))
            elif gate.op == nxgate_op_t.COND:
                assert len(gate.inputs) == 3
                fh.write(
                    f"{signame(gate.inputs[0])} "
                    f"? {signame(gate.inputs[1])} "
                    f": {signame(gate.inputs[2])}"
                )
            else:
                raise Exception("Unknown gate type!")
        elif len(wire.inputs) == 1:
            fh.write(f"{signame(wire.inputs[0])}")
        else:
            raise Exception(f"Assign does not support {len(wire.inputs)} inputs")
        fh.write(";\n")
    # Drive outputs
    fh.write(f"\n// Drive Outputs\n\n")
    for port in module.ports:
        if port.port_type != nxport_type_t.OUTPUT:
            continue
        assert len(port.inputs) == 1
        fh.write(f"assign {signame(port)} = {signame(port.inputs[0])};\n")
    # Write out the footer
    fh.write(f"\nendmodule : {module.name}\n")
