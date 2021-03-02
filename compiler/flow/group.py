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
from ..models.flop import Flop
from ..models.gate import Gate
from ..models.module import Module

def chase_gate(top, gate, depth=0):
    """ Chase backwards from a gate, collecting a logic cloud.

    Args:
        top  : Top-level module
        gate : The Gate instance to start from
        depth: Number of layers away from the flop input

    Returns: Tuple of gates in the logic cloud, and the inputs
    """
    logic, inputs = [], []
    logic.append((gate, depth))
    for in_bit in gate.inputs:
        if isinstance(in_bit, Gate):
            c_logic, c_inputs = chase_gate(top, in_bit, depth=(depth+1))
        else:
            c_logic, c_inputs = chase_bit(top, in_bit, depth=(depth+1))
        logic  += c_logic
        inputs += c_inputs
    return logic, inputs

def chase_bit(top, bit, depth=0):
    """ Chase backwards from a port bit, collecting a logic cloud.

    Args:
        top  : Top-level module
        bit  : The PortBit instance to start from
        depth: Number of layers away from the flop input

    Returns: Tuple of gates in the logic cloud, and the inputs
    """
    logic, inputs = [], []
    # Identify gates
    if bit.driver and isinstance(bit.driver, Gate):
        c_logic, c_inputs = chase_gate(top, bit.driver, depth=(depth+1))
        logic  += c_logic
        inputs += c_inputs
    # Identify logic cloud inputs
    elif (
        # Constants
        isinstance(bit, Constant) or
        # Primary inputs
        (not bit.driver and bit.port.parent == top) or
        # Flop outputs
        (not bit.driver and isinstance(bit.port.parent, Flop))
    ):
        inputs.append((bit, depth))
    # Unknown
    else:
        raise Exception(f"Unknown bit driver: {bit.driver}")
    return logic, inputs

def group_logic(module):
    """
    Group design into logic clouds and flops such that each group comprises a
    a single output flop being fed by multiple inputs/flops via a logic cloud.

    Args:
        module: The input module

    Returns: A collection of groups
    """
    # Check that a module has been provided
    assert isinstance(module, Module)
    # Check whether the module has been flattened
    if [x for x in module.children if type(x) == Module]:
        raise Exception(f"Module {module.name} has not been flattened")
    # Identify all flops in the design
    all_flops = [x for x in module.children.values() if isinstance(x, Flop)]
    # For each flop, chase back the logic to previous flops/primary inputs
    groups = []
    for flop in all_flops:
        # Check the flop is only single bit
        if flop.input.width != 1 or flop.output.width != 1:
            raise Exception(f"Flop {flop.name} is {flop.input.width} bits wide")
        # Chase back input to previous flops/primary inputs
        logic, inputs = chase_bit(module, flop.input[0])
        groups.append((flop, inputs, logic))
    # Return groupings
    return groups
