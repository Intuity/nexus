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

from collections import defaultdict
from functools import lru_cache
from itertools import product

from tabulate import tabulate

from nxcompile import nxsignal_type_t, NXGate, NXFlop, NXPort, NXConstant, nxgate_op_t

def compile_partition(partition):
    print(f"Compiling partition {partition.id}")
    print(f" - Has {len(partition.all_gates)} gates")
    print()
    # ==========================================================================
    # Constants
    # ==========================================================================
    per_slot = 8

    # ==========================================================================
    # Input Handling
    # ==========================================================================

    # Accumulate inputs based on source partition
    inputs = defaultdict(lambda: set())
    for group in partition.groups:
        for source in group.driven_by:
            inputs[source.partition.id].add(source)
    # Add in any inputs coming from external ports
    inputs["EXT"] = partition.src_ports
    # Assign inputs to slots
    input_slots = []
    input_map   = {}
    for signals in map(list, inputs.values()):
        for offset in range(0, len(signals), per_slot):
            chunk  = signals[offset:offset+per_slot]
            chunk += [None] * (per_slot - len(chunk))
            input_map.update({ y: (len(input_slots), x) for x, y in enumerate(chunk) })
            input_slots.append(chunk)

    # ==========================================================================
    # Output Handling
    # ==========================================================================

    # Accumulate outputs based on target partition
    outputs = defaultdict(lambda: set())
    for group in partition.groups:
        for target in group.drives_to:
            outputs[target.partition.id].add(target)
    # Assign outputs to slots
    output_slots = []
    output_map   = {}
    for signals in map(list, outputs.values()):
        for offset in range(0, len(signals), per_slot):
            chunk  = signals[offset:offset+per_slot]
            chunk += [None] * (per_slot - len(chunk))
            output_map.update({ y: (len(output_slots), x) for x, y in enumerate(chunk) })
            output_slots.append(chunk)

    # ==========================================================================
    # Slot Summary
    # ==========================================================================

    print("Slot Allocation:")
    print(f" - Requires {len(input_slots):3d} input slots")
    print(f" - Requires {len(output_slots):3d} output slots")
    print()

    # ==========================================================================
    # Logic Reductions
    # ==========================================================================

    class Table:

        ID = 0

        def __init__(self, op, inputs, outputs):
            self.id       = Table.ID
            Table.ID     += 1
            self.op       = op
            self.inputs   = inputs
            self.outputs  = outputs

        @property
        def name(self):
            return f"TT{self.id}"

        def explode(self):
            yield self
            for input in self.inputs:
                if isinstance(input, Table):
                    yield from input.explode()

        def display(self):
            print(tabulate(
                [
                    ([y for y in f"{x:0{len(self.inputs)}b}"] + [self.outputs[x]])
                    for x in range(2 ** len(self.inputs))
                ],
                headers=[x.name for x in self.inputs] + ["R"],
            ))

    class Operation:
        def __init__(self, gate, *inputs):
            self.gate   = gate
            self.inputs = inputs

        @property
        def op(self):
            return self.gate.op

        def __repr__(self):
            def name(obj):
                if isinstance(obj, NXPort):
                    return "P:" + obj.name
                elif isinstance(obj, NXFlop):
                    return "F:" + obj.name
                else:
                    return str(obj)
            if self.op == nxgate_op_t.COND:
                return (
                    "(" + name(self.inputs[0]) + ") ? " +
                    "(" + name(self.inputs[1]) + ") : " +
                    "(" + name(self.inputs[2]) + ")"
                )
            elif self.op == nxgate_op_t.NOT:
                return "!(" + name(self.inputs[0]) + ")"
            else:
                op_str = {
                    nxgate_op_t.AND : " & ",
                    nxgate_op_t.OR  : " | ",
                    nxgate_op_t.XOR : " ^ ",
                }[self.op]
                return op_str.join([("(" + name(x) + ")") for x in self.inputs])

        def __str__(self):
            return self.__repr__()

        @lru_cache
        def truth(self, max_vars=3):
            # Compile tables for sub-operations
            sub_tables = { x: x.truth() for x in
                           filter(lambda x: isinstance(x, Operation), self.inputs) }
            # Determine the table for this operation
            variables = []
            results   = []
            # Ternary expression
            if self.op == nxgate_op_t.COND:
                for input in self.inputs:
                    if isinstance(input, Operation):
                        variables.append(sub_tables[input])
                    else:
                        variables.append(input)
                # Fixed result of A ? B : C
                results = [0, 1, 0, 1, 0, 0, 1, 1]
            elif self.op == nxgate_op_t.NOT:
                assert len(self.inputs) == 1
                if isinstance(self.inputs[0], Operation):
                    table     = sub_tables[self.inputs[0]]
                    variables = table.inputs
                    results   = [[1, 0][x] for x in table.outputs]
                else:
                    variables.append(self.inputs[0])
                    results = [1, 0]
            else:
                assert len(self.inputs) == 2
                tmp_vars   = []
                tmp_chunks = []
                for input in self.inputs:
                    if isinstance(input, Operation):
                        tmp_vars.append(sub_tables[input])
                    else:
                        tmp_vars.append(input)
                    tmp_chunks.append([0, 1])
                # Consider merging tables
                chunks = []
                for variable, chunk in zip(tmp_vars, tmp_chunks):
                    if isinstance(variable, Table) and (len(variables) + len(variable.inputs) <= max_vars):
                        variables += variable.inputs
                        chunks.append(variable.outputs)
                    else:
                        variables.append(variable)
                        chunks.append(chunk)
                for lhs, rhs in product(*chunks):
                    if self.op == nxgate_op_t.AND:
                        results.append(lhs & rhs)
                    elif self.op == nxgate_op_t.OR:
                        results.append(lhs | rhs)
                    elif self.op == nxgate_op_t.XOR:
                        results.append(lhs ^ rhs)
                    else:
                        raise Exception("UNKNOWN OP!")
            # Return variables and results
            return Table(self, variables, results)

    @lru_cache
    def chase(signal):
        if signal.is_type(nxsignal_type_t.WIRE):
            return chase(signal.inputs[0])
        elif signal.is_type(nxsignal_type_t.GATE):
            all_inputs = list(map(chase, signal.inputs))
            gate       = NXGate.from_signal(signal)
            return Operation(gate, *all_inputs)
        elif signal.is_type(nxsignal_type_t.FLOP):
            return NXFlop.from_signal(signal)
        elif signal.is_type(nxsignal_type_t.PORT):
            return NXPort.from_signal(signal)
        elif signal.is_type(nxsignal_type_t.CONSTANT):
            return NXConstant.from_signal(signal).value
        else:
            raise Exception(f"UNKNOWN TYPE: {signal.type}")

    print("Compiling logic cones")
    cones = []
    for idx, group in enumerate(partition.groups):
        print(f"Building logic cones for group {idx}")
        signal = group.target.inputs[0]
        if signal.is_type(nxsignal_type_t.GATE):
            op = chase(signal)
            cones.append((op, op.truth()))
    print(f"{len(cones)} cones compiled")

    tables = sum([list(x.explode()) for _, x in cones], [])
    print(f"{len(tables)} total tables of which {len(set(tables))} are unique")
    breakpoint()
