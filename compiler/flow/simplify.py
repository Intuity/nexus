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

# NOTE: Maybe should look at the Berkeley Espresso library

import string

import boolean

from ..models.constant import Constant
from ..models.gate import Gate, Operation
from ..models import gate
from ..models.port import PortBit

def index_to_symbol(index):
    symbol = ""
    while True:
        symbol  += string.ascii_lowercase[index % len(string.ascii_lowercase)]
        index  //= len(string.ascii_lowercase)
        if index == 0: break
    return symbol

def simplify_group(flop, inputs, logic):
    """ Try to minify the boolean logic cloud from inputs to output.

    Args:
        flop  : The flop being driven
        inputs: Primary inputs/flop driving logic cloud
        logic : Logic cloud
    """
    algebra = boolean.BooleanAlgebra()
    TRUE, FALSE, NOT, AND, OR, symbol = algebra.definition()
    # Create symbols for each input
    in_syms = {}
    sym2bit = {}
    sym_idx = 0
    for input in set([x[0] for x in inputs]):
        if isinstance(input, Constant):
            in_syms[input.name] = TRUE if input.value else FALSE
        else:
            sym_name = index_to_symbol(sym_idx)
            in_syms[input.name] = symbol(sym_name)
            sym2bit[sym_name]   = input
            sym_idx += 1
    # Recursively build expression from the output backwards
    def chase(bit):
        if isinstance(bit, Gate):
            inbound = [chase(x) for x in bit.inputs]
            if bit.op == Operation.INVERT:
                return NOT(*inbound)
            elif bit.op == Operation.AND:
                return AND(*inbound)
            elif bit.op == Operation.NAND:
                return NOT(AND(*inbound))
            else:
                raise Exception(f"Unexpected operation {bit}")
        elif isinstance(bit, PortBit):
            return in_syms[bit.name]
        else:
            raise Exception(f"Unknown type {bit}")
    # Simplify the logical function
    smpl = chase(flop.input[0].driver).simplify()
    # Re-construct gates
    gate_map = {
        "~" : gate.INVERT,
        "&" : gate.AND,
        "|" : gate.OR,
        "~&": gate.NAND,
        "~|": gate.NOR,
    }
    all_ips = []
    cloud   = []
    def reconstruct(node, depth=0):
        gate_type = None
        node_ips  = []
        # Build and connect a gate
        def build(gate_type, node_ips):
            # Construct the gate
            inst = gate_type(node_ips[0] if gate_type == gate.INVERT else node_ips, None)
            cloud.append((inst, depth))
            # Connect up the outputs of the inputs
            for bit in node_ips:
                if isinstance(bit, gate.Gate):
                    bit.outputs.append(inst)
                else:
                    bit.add_target(inst)
            # Return constructed gate
            return inst
        # Map expression inputs back to port bits
        if isinstance(node, boolean.Symbol):
            all_ips.append(bit := sym2bit[node.obj])
            return bit
        # Break apart multi-input gates into 2-input gates (associative law)
        elif node.operator in ("&", "|") and len(node.args) > 2:
            gate_type = gate_map[node.operator]
            last      = build(gate_type, [reconstruct(x, depth+1) for x in node.args[:2]])
            for arg in node.args[2:]:
                last = build(gate_type, [last, reconstruct(arg, depth+1)])
            return last
        else:
            return build(
                gate_type=gate_map[node.operator],
                node_ips =[reconstruct(x, depth+1) for x in node.args],
            )
    result = reconstruct(smpl)
    # Check if there has been an improvement?
    if len(cloud) > len(logic): return flop, inputs, logic
    # Update the flop to be driven from the simplified logic
    flop.input[0].clear_driver()
    flop.input[0].driver = result
    # Sort the logic cloud by descending depth
    cloud = sorted(cloud, key=lambda x: x[1], reverse=True)
    # Return the updated group
    max_depth = max(x[1] for x in cloud)
    return flop, [(x, max_depth+1) for x in all_ips], cloud
