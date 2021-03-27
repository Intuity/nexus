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

def chase_to_targets(bit):
    """ Chase a driven bit to its ultimate targets.

    Args:
        bit: The starting point

    Returns: List of ultimate targets """
    if isinstance(bit, PortBit):
        if bit.targets:
            return sum([chase_to_targets(x) for x in bit.targets], [])
        else:
            return [bit]
    else:
        return [bit]

def shatter_flops(module):
    """ Shatter multi-bit flops of all children within this module """
    to_remove = []
    for flop in list(module.children.values()):
        if isinstance(flop, Flop) and flop.input.width > 1:
            to_remove.append(flop)
            for bit_idx, (in_bit, out_bit, inv_bit) in enumerate(zip(
                flop.input.bits,
                flop.output.bits     if flop.output     else ([None] * len(flop.input.bits)),
                flop.output_inv.bits if flop.output_inv else ([None] * len(flop.input.bits)),
            )):
                bit_flop = Flop(
                    f"{flop.name}_{bit_idx}",
                    clock     =Port(flop.clock.name,      PortDirection.INPUT,  1),
                    reset     =Port(flop.reset.name,      PortDirection.INPUT,  1) if flop.reset else None,
                    input     =Port(flop.input.name,      PortDirection.INPUT,  1),
                    output    =Port(flop.output.name,     PortDirection.OUTPUT, 1) if flop.output else None,
                    output_inv=Port(flop.output_inv.name, PortDirection.OUTPUT, 1) if flop.output_inv else None,
                )
                module.children[bit_flop.name] = bit_flop
                bit_flop.parent                = module
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
        elif isinstance(flop, Module):
            shatter_flops(flop)
    # Clear up shattered flops
    for flop in to_remove:
        del module.children[flop.name]
        if flop.clock[0] in flop.clock[0].driver.targets:
            flop.clock[0].driver.remove_target(flop.clock[0])
        if flop.reset and flop.reset[0] in flop.reset[0].driver.targets:
            flop.reset[0].driver.remove_target(flop.reset[0])
        for in_bit in flop.input.bits:
            if isinstance(in_bit.driver, Gate):
                in_bit.driver.outputs = [
                    x for x in in_bit.driver.outputs if
                    not isinstance(x, PortBit) or x.port.parent != flop
                ]
            else:
                for tgt in [
                    x for x in in_bit.driver.targets if
                    isinstance(x, PortBit) and x.port.parent == flop
                ]:
                    in_bit.driver.remove_target(tgt)

def flatten_connections(module):
    """ Flatten connectivity of all children within this module """
    for child in module.children.values():
        if isinstance(child, Gate):
            child.inputs  = [chase_to_source(x) for x in child.inputs]
            child.outputs = sum([chase_to_targets(x) for x in child.outputs], [])
        elif isinstance(child, Flop):
            # Resolve clock
            true_clock = chase_to_source(child.clock[0])
            child.clock[0].clear_driver()
            child.clock[0].driver = true_clock
            true_clock.add_target(child.clock[0])
            # Resolve reset
            true_reset = chase_to_source(child.reset[0])
            child.reset[0].clear_driver()
            child.reset[0].driver = true_reset
            true_reset.add_target(child.reset[0])
            # Resolve inputs
            for bit in child.input.bits:
                true_source = chase_to_source(bit.driver)
                bit.clear_driver()
                bit.driver = true_source
                if isinstance(true_source, Gate) and bit not in true_source.outputs:
                    true_source.outputs.append(bit)
                elif isinstance(true_source, PortBit) and bit not in true_source.targets:
                    true_source.add_target(bit)
            # Resolve outputs
            for bit in (child.output.bits if child.output else []):
                true_targets = sum([chase_to_targets(x) for x in bit.targets], [])
                bit.clear_targets()
                for tgt in true_targets:
                    bit.add_target(tgt)
                    if isinstance(tgt, PortBit):
                        tgt.clear_driver()
                        tgt.driver = bit
            # Resolve inverted outputs
            for bit in (child.output_inv.bits if child.output_inv else []):
                true_targets = sum([chase_to_targets(x) for x in bit.targets], [])
                bit.clear_targets()
                for tgt in true_targets:
                    bit.add_target(tgt)
                    if isinstance(tgt, PortBit):
                        tgt.clear_driver()
                        tgt.driver = bit
        elif isinstance(child, Module):
            flatten_connections(child)

def flatten_hierarchy(module):
    """ Flatten module hierarchy, promoting gates and flops """
    # Run through all children
    for child in list(module.children.values()):
        if not isinstance(child, Flop) and not isinstance(child, Gate):
            # Promote grandchildren
            for subchild in flatten_hierarchy(child):
                subchild.name = child.name + "_" + subchild.name
                assert subchild.name not in module.children
                module.children[subchild.name] = subchild
            # Delete this node
            del module.children[child.name]
    # Update all parent pointers
    for child in module.children.values():
        if isinstance(child, Module): child.parent = module
    # Return the list of nodes to promote
    return [
        x for x in module.children.values() if
        isinstance(x, Gate) or isinstance(x, Flop)
    ]

def flatten(module):
    """ Recursively flatten a hierarchical design into a monolithic block.

    Args:
        module: The input Module instance

    Returns: Flattened Module instance.
    """
    assert isinstance(module, Module)
    # Shatter multi-bit flops into many single bit flops
    shatter_flops(module)
    # Flatten connectivity of intermediate modules
    flatten_connections(module)
    # Flatten the hierarchy
    flatten_hierarchy(module)
    # Strip hierarchical connectivity from boundary I/O
    for port in module.ports.values():
        for bit in port.bits:
            to_keep = [
                x for x in bit.targets if
                (not isinstance(x, PortBit)) or
                (isinstance(x.port.parent, Flop)) or
                (type(x.port.parent) == Module and x.port.parent == module)
            ]
            bit.clear_targets()
            for tgt in to_keep: bit.add_target(tgt)
    # Return the flattened module
    return module
