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

from ..models.constant import Constant
from ..models.gate import Gate, Operation
from ..models.flop import Flop
from ..models.port import PortBit

def export_rtl(module, path):
    """ Write out a logic module to Verilog for simulation.

    Args:
        module: The logic module to export
        path  : The path to write the generated Verilog to
    """
    # Check this is a simple module (only contains flops & gates)
    assert len([
        x for x in module.children.values()
        if not isinstance(x, Flop) and not isinstance(x, Gate)
    ]) == 0

    # Create the module declaration
    data = []
    data.append(f"module {module.name} (")
    for idx, port in enumerate(module.ports.values()):
        dirx = "input " if port.is_input else "output"
        size = f"[{port.width-1:3d}:0]" if port.width > 1 else "       "
        data.append(f"    {',' if idx else ' '} {dirx} wire {size} {port.name}")
    data += [");", ""]

    # Calculate a safe name for port bits
    def safe_name(bit):
        return bit.port.hier_name.translate(str.maketrans("$.", "__"))

    # Create flops
    data.append("// Flops")
    for child in module.children.values():
        if not isinstance(child, Flop): continue
        clock = child.clock[0].driver.port.name
        reset = child.reset[0].driver.port.name
        data.append(f"wire {safe_name(child.input[0])};")
        if child.output:
            data.append(f"reg {safe_name(child.output[0])};")
            data.append(f"always @(posedge {clock}, posedge {reset}) begin")
            data.append(f"    if ({reset}) {safe_name(child.output[0])} <= 1'b0;")
            data.append(f"    else {safe_name(child.output[0])} <= {safe_name(child.input[0])};")
            data += ["end", ""]
        if child.output_inv:
            data.append(f"reg {safe_name(child.output_inv[0])};")
            data.append(f"always @(posedge {clock}, posedge {reset}) begin")
            data.append(f"    if ({reset}) {safe_name(child.output_inv[0])} <= 1'b0;")
            data.append(f"    else {safe_name(child.output_inv[0])} <= !{safe_name(child.input[0])};")
            data += ["end", ""]

    # Create gates
    data.append("// Gates")
    for child in module.children.values():
        if not isinstance(child, Gate): continue
        line = f"wire {child.op.name}_{child.id}{' '*(6-len(child.op.name))} = "
        if child.op in (Operation.INVERT, Operation.NAND, Operation.NOR, Operation.XNOR):
            line += "!"
        else:
            line += " "
        line += "("
        for idx, input in enumerate(child.inputs):
            join_op = (" " + {
                Operation.INVERT: "",
                Operation.AND   : "&&",
                Operation.NAND  : "&&",
                Operation.OR    : "||",
                Operation.NOR   : "||",
                Operation.XOR   : "^",
                Operation.XNOR  : "^",
            }[child.op] + " ") if idx > 0 else ""
            if isinstance(input, Gate):
                line += f"{join_op}{input.op.name}_{input.id}"
            elif isinstance(input, Constant):
                line += f"{join_op}{input.value}"
            elif isinstance(input, PortBit):
                line += f"{join_op}{safe_name(input)}"
            else:
                raise Exception(f"Unsupported input {input}")
        line += ");"
        data.append(line)
    data.append("")

    # Link flops to gates
    data.append("// Link gate outputs")
    for child in module.children.values():
        if not isinstance(child, Gate): continue
        for output in child.outputs:
            if isinstance(output, Gate): continue
            data.append(f"assign {safe_name(output)} = {child.op.name}_{child.id};")
    data.append("")

    # Link outputs
    data.append("// Linking outputs")
    for output in (x for x in module.ports.values() if x.is_output):
        data.append(f"assign {output.name} = {'{'}")
        for idx, bit in enumerate(sorted(output.bits, key=lambda x: x.index, reverse=True)):
            data.append("    " + (", " if idx > 0 else "  ") + (
                safe_name(bit.driver)
                if isinstance(bit.driver, PortBit) else
                f"{bit.driver.op.name}_{bit.driver.id}"
            ))
        data.append("};")

    # End the module
    data += ["", "endmodule", ""]
    with open(path, "w") as fh:
        fh.write("\n".join(data))
