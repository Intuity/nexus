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

import itertools
import logging

from ..models.constant import Constant
from ..models.flop import Flop
from ..models.gate import Gate, INVERT, AND, NAND, OR, NOR, XOR, XNOR
from ..models.module import Module
from ..models.port import PortBit

log = logging.getLogger("compiler.simplify")

def simplify(module):
    """
    Simplify the design by merging duplicate gates and propagating constants.

    Args:
        module: The flatted module to simplify

    Returns: Simplified module
    """
    # Create working copy of the module
    assert isinstance(module, Module)
    module = module.copy()

    # Check for duplicate entries of a child, merge if found
    terms = {}
    for child in module.children.values():
        if not isinstance(child, Gate): continue
        if str(child) not in terms: terms[str(child)] = []
        terms[str(child)].append(child)

    for sig, gates in terms.items():
        # Skip items with only one occurence
        if len(gates) == 1: continue
        # Merge items that occur multiple times
        log.debug(f"Merging {len(gates)} duplicates for gate {gates[0]}")
        for gate in gates[1:]:
            for output in gate.outputs:
                gates[0].outputs.append(output)
                if isinstance(output, Gate):
                    output.inputs[output.inputs.index(gate)] = gates[0]
                elif isinstance(output, PortBit):
                    output.clear_driver()
                    output.driver = gates[0]
            for input in gate.inputs:
                if isinstance(input, Gate):
                    input.outputs.remove(gate)
                elif isinstance(input, PortBit):
                    input.remove_target(gate)
            # Remove the duplicate gate
            module.remove_child(gate)

    # Iterate until no further simplifications can be made
    num_smpl = -1
    for iteration in itertools.count(0, 1):
        # Break out if no simplifications were made on the last pass
        if num_smpl == 0: break
        # Reset the counter
        num_smpl = 0
        # Examine every gate in the design
        for gate in [x for x in module.children.values() if isinstance(x, Gate)]:
            in_signal = [x for x in gate.inputs if not isinstance(x, Constant)]
            in_consts = [x.value for x in gate.inputs if isinstance(x, Constant)]
            # Skip gates that aren't driven by a constant
            if not in_consts: continue
            # Only works for 1 and 2 input gates
            assert len(gate.inputs) in (1, 2)
            # Count the simplification
            num_smpl += 1
            # Based on the operation, simplify the gate
            # - INVERT gate - propagate signal value
            if isinstance(gate, INVERT):
                new_const = Constant(0 if in_consts[0] else 1)
                for out in gate.outputs:
                    new_const.add_target(out)
                    if isinstance(out, Gate):
                        out.inputs[out.inputs.index(gate)] = new_const
                    elif isinstance(out, PortBit):
                        out.clear_driver()
                        out.driver = new_const
                    else:
                        raise Exception(f"Unsupported output: {out}")
                # Strip this gate from the hierarchy
                module.remove_child(gate)
                for input in gate.inputs:
                    if isinstance(input, Gate):
                        input.outputs.remove(gate)
                        assert gate not in input.outputs
                    elif isinstance(input, PortBit):
                        input.remove_target(gate)
                        assert gate not in input.targets
                    else:
                        raise Exception(f"Unsupported input: {input}")
            # - AND gate - propagate constant, or unmodified value
            elif isinstance(gate, AND):
                # If a 0 is present or no input signals, tie output value
                if (0 in in_consts) or (len(in_signal) == 0):
                    new_const = Constant(0 if (0 in in_consts) else 1)
                    for out in gate.outputs:
                        new_const.add_target(out)
                        if isinstance(out, Gate):
                            out.inputs[out.inputs.index(gate)] = new_const
                        elif isinstance(out, PortBit):
                            out.clear_driver()
                            out.driver = new_const
                        else:
                            raise Exception(f"Unsupported output: {out}")
                # Otherwise, pass input through unmodified
                else:
                    assert len(in_signal) == 1
                    for out in gate.outputs:
                        # Link the upstream source directly to the target
                        if isinstance(in_signal[0], Gate):
                            in_signal[0].outputs.append(out)
                        elif isinstance(in_signal[0], PortBit):
                            in_signal[0].add_target(out)
                        # Reconnect the downstream target directly to the source
                        if isinstance(out, Gate):
                            out.inputs[out.inputs.index(gate)] = in_signal[0]
                        elif isinstance(out, PortBit):
                            out.clear_driver()
                            out.driver = in_signal[0]
                        else:
                            raise Exception(f"Unsupported output: {out}")
                # Strip this gate from the hierarchy
                module.remove_child(gate)
                for input in gate.inputs:
                    if isinstance(input, Gate):
                        input.outputs.remove(gate)
                        assert gate not in input.outputs
                    elif isinstance(input, PortBit):
                        input.remove_target(gate)
                        assert gate not in input.targets
                    else:
                        raise Exception(f"Unsupported input: {input}")
            # - NAND gate - propagate constant, or inverted value
            elif isinstance(gate, NAND):
                # If 0 present -> tie output high, if both inputs = 1 -> tie low
                if (0 in in_consts) or (len(in_signal) == 0 and (0 not in in_consts)):
                    # Disconnect upstream source
                    if in_signal:
                        if isinstance(in_signal[0], Gate):
                            in_signal[0].outputs.remove(gate)
                        elif isinstance(in_signal[0], PortBit):
                            in_signal[0].remove_target(gate)
                    # Drive targets from the constant
                    new_const = Constant(1 if (0 in in_consts) else 0)
                    for out in gate.outputs:
                        new_const.add_target(out)
                        if isinstance(out, Gate):
                            out.inputs[out.inputs.index(gate)] = new_const
                        elif isinstance(out, PortBit):
                            out.clear_driver()
                            out.driver = new_const
                        else:
                            raise Exception(f"Unsupported output: {out}")
                # If a 1 is present, invert the other signal
                elif (1 in in_consts):
                    # Drop the target from the existing connection
                    if isinstance(in_signal[0], Gate):
                        in_signal[0].outputs.remove(gate)
                    elif isinstance(in_signal[0], PortBit):
                        in_signal[0].remove_target(gate)
                    # Check if the required inverter doesn't already exist?
                    new_inv = INVERT(in_signal[0])
                    found   = [x for x in module.children.values() if str(x) == str(new_inv)]
                    new_inv = found[0] if found else new_inv
                    # Reconnect the upstream source to the new inverter
                    if not found:
                        module.add_child(new_inv)
                        if isinstance(in_signal[0], Gate):
                            in_signal[0].outputs.append(new_inv)
                        elif isinstance(in_signal[0], PortBit):
                            in_signal[0].add_target(new_inv)
                    # Reconnect the downstream targets to the new inverter
                    for out in gate.outputs:
                        new_inv.outputs.append(out)
                        if isinstance(out, Gate):
                            out.inputs[out.inputs.index(gate)] = new_inv
                        elif isinstance(out, PortBit):
                            out.clear_driver()
                            out.driver = new_inv
                        else:
                            raise Exception(f"Unsupported output: {out}")
                # Strip this gate from the hierarchy
                module.remove_child(gate)
            # - Other gates are unsupported
            else:
                raise Exception(f"Unsupported gate: {gate}")
        # Identify chains of inverters
        inv_chains = []
        for gate in [x for x in module.children.values() if isinstance(x, INVERT)]:
            # If the input to the inverter is not an inverter, ignore
            if not isinstance(gate.inputs[0], INVERT): continue
            # Count how many inverters are in series
            def chase(gate):
                if not isinstance(gate.inputs[0], INVERT): return (1, [gate])
                count, chain = chase(gate.inputs[0])
                return (count + 1), chain + [gate]
            count, chain = chase(gate)
            inv_chains.append((gate, count, chain))
        # Collapse chains of inverters (from longest to shortest)
        for gate, count, chain in sorted(inv_chains, key=lambda x: x[1], reverse=True):
            log.debug(f"Flattening {count} step inverter chain")
            # Keep track of simplifications
            num_smpl += 1
            # Equal number -> no invert, odd number -> invert
            new_source = chain[0].inputs[0] if ((count % 2) == 0) else chain[0]
            # Reconnect outputs to the new source
            for out in gate.outputs:
                # Connect outputs back to original input
                if isinstance(out, Gate):
                    out.inputs[out.inputs.index(gate)] = new_source
                elif isinstance(out, PortBit):
                    out.clear_driver()
                    out.driver = new_source
                else:
                    raise Exception(f"Unknown tartget: {out}")
                # Add the connection to the new source
                if isinstance(new_source, Gate):
                    new_source.outputs.append(out)
                elif isinstance(new_source, PortBit):
                    new_source.add_target(out)
                else:
                    raise Exception(f"Unknown source: {new_source}")
            # Unlink from previous link in the chain
            gate.inputs[0].outputs.remove(gate)
            # Remove gate from module
            module.remove_child(gate)
        # Simplify flops if state is being driven by a constant
        for flop in [x for x in module.children.values() if isinstance(x, Flop)]:
            # Skip flops which are not driven by a constant
            if not isinstance(flop.input[0].driver, Constant): continue
            # Count the simplification
            num_smpl += 1
            # Propagate the constant through the flop
            const = flop.input[0].driver
            for tgt in flop.output[0].targets:
                const.add_target(tgt)
                if isinstance(tgt, Flop):
                    tgt.input[0].clear_driver()
                    tgt.input[0].driver = const
                elif isinstance(tgt, Gate):
                    tgt.inputs[tgt.inputs.index(flop.output[0])] = const
            # Unlink flop from the constant
            const.remove_target(flop.input[0])
            # Drop flop from the module's children
            module.remove_child(flop)
        # Log progress made
        log.info(f"Simplification pass {iteration} - made {num_smpl} simplifications")
    # Return the simplified module
    return module
