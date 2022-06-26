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
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import Tuple

from tabulate import tabulate

from nxcompile import nxsignal_type_t, NXGate, NXFlop, NXPort, NXConstant, nxgate_op_t
from nxisa import Load, Store, Branch, Send, Truth, Arithmetic, Shuffle

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
        for input in self.inputs:
            if isinstance(input, Table):
                yield from input.explode()
        yield self

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
            # If number of variables has exceeded limit, revert to base
            if len(variables) > max_vars:
                variables = tmp_vars
                chunks    = tmp_chunks
            # Construct the results based on chunks
            for lhs, rhs in product(*chunks):
                if self.op == nxgate_op_t.AND:
                    results.append(lhs & rhs)
                elif self.op == nxgate_op_t.OR:
                    results.append(lhs | rhs)
                elif self.op == nxgate_op_t.XOR:
                    results.append(lhs ^ rhs)
                else:
                    raise Exception("UNKNOWN OP!")
        # Sanity check
        assert len(variables) <= max_vars
        # Return variables and results
        return Table(self, variables, results)

class MemorySlot:

    def __init__(self, row, index, paired=None):
        self.row      = row
        self.index    = index
        self.paired   = paired
        self.elements = [None] * 8

class MemoryRow:

    def __init__(self, memory, index):
        self.memory = memory
        self.index  = index
        self.slots  = [MemorySlot(self, x) for x in range(4)]

    def pair(self, start_idx):
        assert (start_idx % 2) == 0, f"Can't pair slot index {start_idx}"
        self.slots[start_idx  ].paired = self.slots[start_idx+1]
        self.slots[start_idx+1].paired = self.slots[start_idx  ]

class Memory:

    def __init__(self):
        self.rows      = [MemoryRow(self, 0)]
        self.last_row  = 0
        self.last_slot = 0
        self.last_bit  = 0
        self.mapping   = {}

    @property
    def row(self):
        return self.rows[self.last_row]

    @property
    def slot(self):
        return self.rows[self.last_row].slots[self.last_slot]

    def bump_row(self) -> MemoryRow:
        self.rows.append(MemoryRow(self, self.last_row))
        self.last_row  += 1
        self.last_slot  = 0
        return self.rows[-1]

    def bump_slot(self):
        self.last_slot += 1
        self.last_bit   = 0
        if self.last_slot >= 4:
            self.bump_row()

    def align(self, is_seq):
        align16 = ((self.last_slot % 2) == 0)
        paired  = (self.slot.paired is not None)
        # For sequential placements...
        if is_seq:
            # If not aligned to a 16-bit boundary, then align up
            if not align16:
                self.bump_slot()
                paired = (self.slot.paired is not None)
            # If aligned but not paired...
            if not paired:
                # If some elements already in slot, bump by two slots
                if self.last_bit > 0:
                    self.bump_slot()
                    self.bump_slot()
                # Pair the slot and its neighbour
                self.row.pair(self.last_slot)
        # For combinatorial placements, if paired then bump to the next free slot
        elif paired:
            self.bump_slot()
            self.bump_slot()

    def place(self, signal, is_seq):
        # Align to the next suitable point
        self.align(is_seq)
        # Place signal in the slot
        self.slot.elements[self.last_bit] = signal
        # Track where signal has been placed
        self.mapping[signal.name] = (self.last_row, self.last_slot, self.last_bit)
        # Increment bit position
        self.last_bit += 1
        if self.last_bit >= 8:
            self.bump_slot()
        # Return the placement
        return self.mapping[signal.name]

    def place_all(self, signals, is_seq, clear=False):
        if clear and self.last_bit > 0:
            self.bump_slot()
        start_row, start_slot = self.last_row, self.last_slot
        for sig in signals:
            if sig is not None:
                self.place(sig, is_seq)
        return start_row, start_slot

    def find(self, signal, default=None):
        return self.mapping.get(signal.name, default)

def assign_inputs(partition, memory):
    # Accumulate inputs based on source partition
    # NOTE: Excludes signals from own partition
    inputs = defaultdict(lambda: set())
    for group in partition.groups:
        for source in group.driven_by:
            if source.partition.id != partition.id:
                inputs[source.partition.id].add(source.target)
    # Also include inputs coming from external ports
    inputs["EXT"] = partition.src_ports
    # Assign inputs to slots in the memory
    num_slots = 0
    for signals in filter(lambda x: len(x) > 0, map(list, inputs.values())):
        for offset in range(0, len(signals), 8):
            # TODO: Cope with combinatorial sources
            memory.place_all(signals[offset:offset+8], True)
            num_slots += 1
        # Bump to avoid mixing signals from different source partitions
        memory.bump_slot()
    # Bump and align to make next placement safe
    if memory.last_bit != 0:
        memory.bump_slot()
    memory.align(True)
    return num_slots

def assign_flops(partition, memory):
    all_target = list(partition.tgt_flops)
    num_slots = 0
    for offset in range(0, len(all_target), 8):
        memory.place_all(all_target[offset:offset+8], True)
        num_slots += 1
    # Bump and align to make placement safe
    if memory.last_bit != 0:
        memory.bump_slot()
    memory.align(True)
    return num_slots

def assign_outputs(partition):
    # Accumulate outputs based on target partition
    outputs = defaultdict(lambda: set())
    for group in partition.groups:
        for target in group.drives_to:
            outputs[target.partition.id].add(target.target)
    # Assign outputs to slots
    output_slots = []
    output_map   = {}
    for signals in map(list, outputs.values()):
        for offset in range(0, len(signals), 8):
            chunk  = signals[offset:offset+8]
            output_map.update({ y.name: (len(output_slots), x) for x, y in enumerate(chunk) })
            chunk += [None] * (8 - len(chunk))
            output_slots.append(chunk)
    return output_map, output_slots

def identify_operations(partition):
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

    cones = []
    for group in partition.groups:
        signal = group.target.inputs[0]
        if signal.is_type(nxsignal_type_t.GATE):
            op = chase(signal)
            cones.append((op, op.truth()))
    print(f" - Compiled {len(cones)} logic cones")

    tables = list(sorted(set(sum([list(x.explode()) for _, x in cones], [])), key=lambda x: x.id))
    uses   = { t: tables.count(t) for t in set(tables) }
    print(f"   + {len(tables)} total tables of which {len(uses.keys())} are unique")
    print(f"   + {len(set([''.join(map(str, x.outputs)) for x in uses.keys()]))} unique encodings")
    print()

    # Sort cones into an order where they are always satisified
    satisfied  = []
    last_count = len(tables)
    while tables:
        to_drop = []
        for idx, table in enumerate(tables):
            if any(x for x in table.inputs if isinstance(x, Table) and x not in satisfied):
                if last_count == 89:
                    breakpoint()
                continue
            satisfied.append(table)
            to_drop.append(idx)
        tables = [x for i, x in enumerate(tables) if i not in to_drop]
        assert len(tables) != last_count
        last_count = len(tables)

    return satisfied, uses


def compile_partition(partition):
    print(f"Compiling partition {partition.id}")
    print(f" - Has {len(partition.all_gates)} gates")
    print()

    # Create a memory
    memory = Memory()

    # Assign input slots
    num_input_slots          = assign_inputs(partition, memory)
    num_flop_slots           = assign_flops(partition, memory)
    output_map, output_slots = assign_outputs(partition)

    print("Slot Allocation:")
    print(f" - Requires {num_input_slots:3d} input slots")
    print(f" - Requires {num_flop_slots:3d} flop slots")
    print(f" - Requires {len(output_slots):3d} output slots")

    # Identify all of the logic tables
    tables, uses = identify_operations(partition)

    class Register:

        def __init__(self, index, width=8):
            self.index    = 0
            self.elements = [None] * width
            self.age      = 0
            self.active   = False

        def __getitem__(self, key):
            return self.elements[key]

        def __setitem__(self, key, val):
            self.elements[key]

        def activate(self):
            self.active = True

        def deactivate(self):
            self.active = False

        def aging(self):
            self.age = (self.age + 1) if self.active else 0

        def __iter__(self):
            return self.elements

    # Track register usage
    registers = [Register(index=x) for x in range(8)]

    def select_register(exclude=None):
        nonlocal registers
        exclude = exclude or []
        # First look for inactive registers
        try:
            return next(x for x in registers if not x.active and x not in exclude)
        # If no inactive registers available, select the oldest
        except StopIteration:
            return next(iter(sorted([x for x in registers if x not in exclude],
                                    key=lambda x: x.age,
                                    reverse=True)))

    def emit_register_reuse(register):
        # TODO: Check that any of the values actually need to be preserved
        if register.active:
            row, slot = memory.place_all(register.elements, False, True)
            yield Store(src    =register.index,
                        mask   =0xFF,
                        slot   =(slot // 2),
                        address=row,
                        offset =(2 | (slot % 2)))
        register.activate()
        register.age = 0

    def emit_source_setup(signal, exclude=None):
        nonlocal registers
        exclude = exclude or []
        # Search for this signal in the registers
        for reg in registers:
            if signal not in reg.elements:
                continue
            if (bit_idx := reg.elements.index(signal)) != 0:
                # If this register is protected, shuffle into a different one
                if reg in exclude:
                    new_reg = select_register(exclude)
                    yield from emit_register_reuse(new_reg)
                    yield Shuffle(src=reg.index, tgt=new_reg.index, mux=[
                        { 0: bit_idx, bit_idx: 0 }.get(i, i) for i in range(8)
                    ])
                    new_reg.elements = reg.elements[:]
                    new_reg.elements[0], new_reg.elements[bit_idx] = new_reg.elements[bit_idx], new_reg.elements[0]
                # If this register is not protected, shuffle it
                else:
                    yield Shuffle(src=reg.index, tgt=reg.index, mux=[
                        { 0: bit_idx, bit_idx: 0 }.get(i, i) for i in range(8)
                    ])
                    reg.elements[0], reg.elements[bit_idx] = reg.elements[bit_idx], reg.elements[0]
            break
        # If not found, then try to load in from memory
        else:
            tgt = select_register(exclude)
            yield from emit_register_reuse(tgt)
            # Search in memory
            if mapping := memory.find(signal):
                row, slot, bit_idx = mapping
                yield Load(tgt    =tgt.index,
                           slot   =(slot // 2),
                           address=row,
                           offset =(2 | (slot % 2)))
                for idx, entry in enumerate(memory.rows[row].slots[slot].elements):
                    tgt.elements[idx] = entry
                if bit_idx != 0:
                    yield Shuffle(src=tgt.index, tgt=tgt.index, mux=[
                        { 0: bit_idx, bit_idx: 0 }.get(i, i) for i in range(8)
                    ])
                    tgt.elements[0], tgt.elements[bit_idx] = tgt.elements[bit_idx], tgt.elements[0]
            else:
                # Not found
                raise Exception(f"Failed to locate signal '{signal}'")

    def emit_operation(cone):
        nonlocal registers
        # Perform first stage preparation of registers
        srcs = []
        for input in cone.inputs:
            yield from emit_source_setup(input, exclude=srcs)
            # NOTE: Assuming the required value is placed in bit 0
            srcs.append([x for x in registers if x[0] == input][0])
        # Determine a target register and trigger optional reuse
        tgt = select_register(exclude=srcs)
        yield from emit_register_reuse(tgt)
        # Extract and pad the lookup table
        table = 0
        if len(cone.inputs) == 1:
            srcs  = [srcs[0].index, 0, 0]
            table = sum([(x << i) for i, x in enumerate(cone.outputs * 4)])
        elif len(cone.inputs) == 2:
            srcs  = [srcs[0].index, srcs[1].index, 0]
            table = sum([(x << i) for i, x in enumerate(cone.outputs * 2)])
        elif len(cone.inputs) == 3:
            srcs = [x.index for x in srcs]
            table = sum([(x << i) for i, x in enumerate(cone.outputs)])
        else:
            raise Exception("Unsupported number of inputs")
        if table > 0xFF:
            breakpoint()
        # Emit an instruction
        yield Truth(src=srcs, tgt=tgt.index, imm=0, si=0, table=table)
        tgt.elements = [cone] + ([None] * 7)

    # Assemble the instruction stream
    stream = []
    for table in tables:
        for instr in emit_operation(table):
            stream.append(instr)
            print(f">>> I{len(stream):04d}: {instr.to_asm():40} -> 0x{instr.encode():08X}")
            for reg in registers:
                reg.aging()
