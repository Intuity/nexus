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

from ..models.flop import Flop
from ..models.gate import Gate, INVERT, AND, NAND, OR, NOR, XOR, XNOR
from ..models.module import Module
from ..models.port import PortBit, Port, PortDirection

def chase_to_source(bit):
    """ Chase driver of a bit back to its source.

    Args:
        bit: The bit being driven

    Returns: The original driver """
    current = bit
    while isinstance(current, PortBit) and current.driver:
        current = current.driver
    return current

def flatten(module, depth=0):
    """ Recursively flatten a hierarchical design into a monolithic block.

    Args:
        module: The input Module instance
        depth : How deep is the recursion

    Returns: Flattened Module instance.
    """
    assert isinstance(module, Module)
    # First flatten all child modules
    promoted = []
    for c_key, child in [x for x in module.children.items()]:
        # Ignore gates and flops - these are handled later
        if isinstance(child, Gate) or isinstance(child, Flop): continue
        # Create a flat child
        f_child = flatten(child, depth=(depth + 1))
        # Reconnect signals on the boundary of the child
        for port in f_child.ports.values():
            for bit in port.bits:
                source = chase_to_source(bit)
                for target in bit.targets:
                    # Adjust the target's driver
                    if isinstance(target, Gate):
                        target.inputs[target.inputs.index(bit)] = source
                    elif isinstance(target, PortBit):
                        target.parent = module
                        target.clear_driver()
                        target.driver = source
                    else:
                        raise Exception(f"Unrecognised target {target}")
                    # Adjust the source's targets
                    if isinstance(source, Gate):
                        source.outputs.append(target)
                    elif isinstance(source, PortBit):
                        source.parent = module
                        source.add_target(target)
                    else:
                        raise Exception(f"Unrecognised source {source}")
        # Promote children up one level
        for grandchild in f_child.children.values():
            grandchild.name = f"{f_child.name}_{grandchild.name}"
            promoted.append(grandchild)
        # Remove the child
        del module.children[c_key]
    # Pickup the promoted modules
    for grandchild in promoted: module.add_child(grandchild)
    # At the top-level, perform some tidying operations
    if depth == 0:
        # Clean-up boundary ports with references to flattened modules
        for port in module.inputs:
            for bit in port.bits:
                to_keep = [
                    x for x in bit.targets
                    if not isinstance(x, PortBit)
                    or not type(x.port.parent) == Module
                    or x.port.parent == module
                ]
                bit.clear_targets()
                for tgt in to_keep: bit.add_target(tgt)
        # Shatter multi-bit flops
        mb_flops = [
            x for x in module.children.values()
            if isinstance(x, Flop) and x.input.width > 1
        ]
        for flop in mb_flops:
            in_bits  = flop.input.bits
            out_bits = flop.output.bits if flop.output else ([None]*len(in_bits))
            inv_bits = flop.output_inv.bits if flop.output_inv else ([None]*len(in_bits))
            for idx, (in_bit, out_bit, inv_bit) in enumerate(zip(in_bits, out_bits, inv_bits)):
                bit_flop = Flop(
                    f"{flop.name}_{idx}",
                    clock     =Port(flop.clock.name,      PortDirection.INPUT,  1),
                    reset     =Port(flop.reset.name,      PortDirection.INPUT,  1) if flop.reset      else None,
                    input     =Port(flop.input.name,      PortDirection.INPUT,  1),
                    output    =Port(flop.output.name,     PortDirection.OUTPUT, 1) if flop.output     else None,
                    output_inv=Port(flop.output_inv.name, PortDirection.OUTPUT, 1) if flop.output_inv else None,
                )
                module.children[bit_flop.name] = bit_flop
                # Link clock
                bit_flop.clock[0].driver = flop.clock[0].driver
                bit_flop.clock[0].driver.add_target(bit_flop.clock[0])
                # Optionally link reset
                if bit_flop.reset:
                    bit_flop.reset[0].driver = flop.reset[0].driver
                    bit_flop.reset[0].driver.add_target(bit_flop.reset[0])
                # Link input
                bit_flop.input[0].driver = in_bit.driver
                if isinstance(bit_flop.input[0].driver, Gate):
                    bit_flop.input[0].driver.outputs.append(bit_flop.input[0])
                else:
                    bit_flop.input[0].driver.add_target(bit_flop.input[0])
                # Optionally link output
                if bit_flop.output:
                    for tgt in out_bit.targets:
                        bit_flop.output[0].add_target(tgt)
                        if isinstance(tgt, Gate):
                            tgt.inputs[tgt.inputs.index(out_bit)] = bit_flop.output[0]
                        else:
                            tgt.clear_driver()
                            tgt.driver = bit_flop.output[0]
                # Optionally link inverted output
                if bit_flop.output_inv:
                    for tgt in inv_bit.targets:
                        bit_flop.output_inv[0].add_target(tgt)
                        if isinstance(tgt, Gate):
                            tgt.inputs[tgt.inputs.index(out_bit)] = bit_flop.output[0]
                        else:
                            tgt.clear_driver()
                            tgt.driver = bit_flop.output_inv[0]
        # Remove shattered flops and unlink input drivers (outputs already unlinked)
        for flop in mb_flops:
            del module.children[flop.name]
            flop.clock[0].driver.remove_target(flop.clock[0])
            if flop.reset: flop.reset[0].driver.remove_target(flop.reset[0])
            if isinstance(flop.input[0].driver, Gate):
                flop.input[0].driver.outputs.remove(flop.input[0])
            else:
                flop.input[0].driver.remove_target(flop.input[0])
    # Return the flattened module
    return module
