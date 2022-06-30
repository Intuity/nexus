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
from math import ceil
from statistics import mean
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

    @property
    def all_inputs(self):
        return self.inputs + sum((x.all_inputs for x in self.inputs if isinstance(x, Table)), [])

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

def assign_flops(partition, memory, tables):
    # Pack results as efficiently as possible
    slots  = []
    cycles = {}
    # Consider table results in chunks of 8
    for idx in range(0, len(tables), 8):
        # Take chunk & reverse it (as results are shifted up the register)
        chunk = tables[idx:idx+8][::-1]
        # Work out which results drive flops
        for cix, entry in enumerate(chunk):
            flops = [x for x in entry.op.gate.outputs if x.is_type(nxsignal_type_t.FLOP)]
            if flops:
                assert len(flops) == 1
                chunk[cix] = flops[0]
            else:
                chunk[cix] = None
        # Try to find a slot with gaps in the right places
        candidates = []
        for slot_idx, slot in enumerate(slots):
            if not any((slot[i] is not None) for i, x in enumerate(chunk) if x is not None):
                candidates.append((slot_idx, slot, len([x for x in slot if x is None])))
        if len(candidates) == 0:
            slots.append([None] * 8)
            candidates.append((len(slots)- 1, slots[-1], 8))
        # Choose the busiest slot
        slot_idx, slot, _ = sorted(candidates, key=lambda x: x[2])[0]
        # Insert flops into the slot
        # NOTE: Use 'idx+8' because this is the operation for which flush occurs
        cycles[idx+8] = (slot_idx, [])
        for cix, entry in enumerate(chunk):
            if entry is not None:
                slot[cix] = entry
                cycles[idx+8][1].append(cix)
        # If no entries recorded
        if not cycles[idx+8][1]:
            del cycles[idx+8]
    # Place any flops which are not driven by tables (constants/pipelining)
    all_flops = sum([[x.name for x in y if x is not None] for y in slots], [])
    for flop in partition.tgt_flops:
        # Skip flops that are already placed
        if flop.name in all_flops:
            continue
        # Search for the first free location
        # NOTE: This won't make stores any more efficient, but is has a chance
        #       of reducing the number of loads
        for slot in slots:
            if None in slot:
                slot[slot.index(None)] = flop
                break
        else:
            slots.append([None] * 8)
            slots[0] = flop
    # Allocate slots in the memory
    targets = []
    for slot in slots:
        targets.append(memory.place_all(slot, is_seq=True, clear=True))
    # Return the slots and cycle encodings
    return slots, cycles, targets

def assign_outputs(partition):
    # Accumulate outputs based on target partition
    outputs = defaultdict(lambda: set())
    for group in partition.groups:
        for target in group.drives_to:
            if target.partition.id != partition.id:
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

    mapping = {}
    for group in partition.groups:
        signal = group.target.inputs[0]
        if signal.is_type(nxsignal_type_t.GATE):
            mapping[signal] = chase(signal).truth()

    # Expand the full set (including tables within tables)
    tables = list(set(sum([list(x.explode()) for x in mapping.values()], [])))

    # Build table-to-table references
    refs = defaultdict(lambda: set())
    for table in tables:
        # Track tables using other tables as inputs
        for input in table.inputs:
            if isinstance(input, Table):
                refs[input].add(table)
        # Track flops consuming a table's output
        for signal in table.op.gate.outputs:
            if signal.name in (x.name for x in partition.tgt_flops):
                refs[table].add(signal)

    # Sort tables by descending complexity
    # NOTE: The intention here is to bias placement in the next step to prefer
    #       completion of complex terms first, rather than evaluating all of the
    #       simple terms
    tables.sort(key=lambda x: len(x.all_inputs), reverse=True)

    # Sort tables into an order where they are always satisified
    # NOTE: It may seem inefficient to only make one placement per pass, but it
    #       has a notable benefit on number of instructions required as this
    #       prefers completing complex terms first
    satisfied = []
    while tables:
        for table in tables:
            if any(x for x in table.inputs if isinstance(x, Table) and x not in satisfied):
                continue
            satisfied.append(table)
            tables.remove(table)
            break
        else:
            raise Exception("Made no progress!")

    return satisfied, refs, mapping


def compile_partition(partition):
    print(f"Compiling partition {partition.id}")
    print(f" - Has {len(partition.all_gates)} gates")
    print()

    # Create a memory
    memory = Memory()

    # Identify all of the logic tables
    tables, references, sig_table_map = identify_operations(partition)

    # Assign input slots
    num_input_slots                       = assign_inputs(partition, memory)
    flop_slots, flop_cycles, flop_targets = assign_flops(partition, memory, tables)
    output_map, output_slots              = assign_outputs(partition)

    print("Slot Allocation:")
    print(f" - Requires {num_input_slots:3d} input slots")
    print(f" - Requires {len(flop_slots):3d} flop slots")
    print(f" - Requires {len(output_slots):3d} output slots")
    print()

    print("Logic Tables:")
    print(f" - Compiled {len(tables):3d} tables")
    print(f" - Referred {sum(map(len, references.values())):3d} times")
    print()

    class Register:

        def __init__(self, index, width=8):
            self.index    = index
            self.elements = [None] * width
            self.age      = 0
            self.active   = False
            self.novel    = False

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
    registers = [Register(index=x) for x in range(7)]

    # Reserve R7 for outputs of truth tables
    reg_work = Register(index=7)

    # Gather the instruction stream
    stream = []

    # Track read/write addresses
    trk_read           = defaultdict(lambda: 0)
    trk_write          = defaultdict(lambda: 0)
    trk_usage          = defaultdict(lambda: [])
    trk_select         = 0
    trk_evict_inactive = 0
    trk_evict_novel    = 0
    trk_evict_notnovel = 0

    def select_register(exclude=None):
        nonlocal registers, trk_select, trk_evict_inactive, trk_evict_novel, trk_evict_notnovel
        exclude     = exclude or []
        trk_select += 1
        # Filter out non-excluded registers
        legal = list(filter(lambda x: (x not in exclude), registers))
        # Look for inactive registers
        if inactive := [x for x in legal if not x.active]:
            trk_evict_inactive += 1
            return inactive[0]
        # Look for the oldest non-novel register
        if notnovel := sorted([x for x in legal if not x.novel], key=lambda x: x.age, reverse=True):
            trk_evict_novel += 1
            return notnovel[0]
        # Finally choose the oldest register
        trk_evict_notnovel += 1
        ordered = sorted(legal, key=lambda x: x.age, reverse=True)
        return ordered[0]

    def emit_register_reuse(register):
        nonlocal trk_write
        if register.active and register.novel:
            # Check if any entries actually need preserving?
            if any((len(references.get(x, [])) > 0) for x in register.elements):
                row, slot = memory.place_all(register.elements, False, True)
                trk_write[(row, slot)] += 1
                trk_usage[(row, slot)].append(("write", len(stream)))
                yield Store(src    =register.index,
                            mask   =0xFF,
                            slot   =(slot // 2),
                            address=row,
                            offset =(2 | (slot % 2)))
        register.activate()
        register.age   = 0
        register.novel = False

    def emit_source_setup(signal, exclude=None):
        nonlocal registers, trk_read
        exclude = exclude or []
        # Search for this signal in the registers
        for reg in registers + [reg_work]:
            if signal.name in (x.name for x in reg.elements if x is not None):
                break
        # If not found, then try to load in from memory
        else:
            tgt = select_register(exclude)
            yield from emit_register_reuse(tgt)
            # Search in memory
            if mapping := memory.find(signal):
                row, slot, _ = mapping
                yield Load(tgt    =tgt.index,
                           slot   =(slot // 2),
                           address=row,
                           offset =(2 | (slot % 2)))
                trk_usage[(row, slot)].append(("read", len(stream)))
                trk_read[(row, slot)] += 1
                tgt.elements = memory.rows[row].slots[slot].elements[:]
            else:
                # Not found
                raise Exception(f"Failed to locate signal '{signal}'")

    def emit_operation(cone_idx, cone):
        nonlocal registers
        # Gather inputs
        srcs = []
        idxs = []
        for input in cone.inputs:
            yield from emit_source_setup(input, exclude=srcs)
            for reg in registers + [reg_work]:
                if input.name in (getattr(x, "name", None) for x in reg.elements):
                    srcs.append(reg)
                    idxs.append([getattr(x, "name", None) for x in reg.elements].index(input.name))
                    break
            else:
                raise Exception("Failed to locate input")
            if isinstance(input, Table):
                references[input].remove(cone)
        # Check if working register has reached a flush point (all registers full)
        if None not in reg_work.elements:
            # Move value out to a target register (uses shuffle but keeps order)
            tgt = select_register(exclude=srcs)
            yield from emit_register_reuse(tgt)
            yield Shuffle(src=reg_work.index, tgt=tgt.index, mux=list(range(8)))
            tgt.elements      = reg_work.elements[:]
            tgt.novel         = True
            reg_work.elements = [None] * 8
            # If this is corresponds to a flop update, perform masked store
            if (selection := flop_cycles.get(cone_idx, None)):
                slot_idx, places = selection
                row, slot        = flop_targets[slot_idx]
                yield Store(src    =reg_work.index,
                            mask   =sum(((1 << x) for x in places)),
                            slot   =(slot // 2),
                            address=row,
                            offset =Store.offset.PRESERVE)
        # Extract and pad the lookup table
        table = 0
        if len(cone.inputs) == 1:
            srcs  = [srcs[0].index, 0, 0]
            idxs  = [idxs[0]]
            table = sum([(x << i) for i, x in enumerate(cone.outputs * 4)])
        elif len(cone.inputs) == 2:
            srcs  = [srcs[0].index, srcs[1].index, 0]
            idxs  = [idxs[0], idxs[1], 0]
            table = sum([(x << i) for i, x in enumerate(cone.outputs * 2)])
        elif len(cone.inputs) == 3:
            srcs  = [x.index for x in srcs]
            table = sum([(x << i) for i, x in enumerate(cone.outputs)])
        else:
            raise Exception("Unsupported number of inputs")
        assert table >= 0 and table <= 0xFF, "Incorrect table value"
        # Emit an instruction
        yield Truth(src=srcs, mux=idxs, table=table, tgt=reg_work.index)
        # Shift working register and insert new value
        reg_work.elements = [cone] + reg_work.elements[:7]

    # Assemble the computation stream
    counts = defaultdict(lambda: 0)
    print("Generating Instruction Stream:")
    print()
    def stream_add(instr):
        stream.append(instr)
        counts[instr.instr.opcode.op_name] += 1
        print(f"[{len(stream):04d}] {instr.to_asm():40} -> 0x{instr.encode():08X}")

    def stream_iter(gen):
        for instr in gen:
            stream_add(instr)
            for reg in registers:
                reg.aging()

    truth_flops = []
    for idx, table in enumerate(tables):
        stream_iter(emit_operation(idx, table))
        for output in table.op.gate.outputs:
            if output.is_type(nxsignal_type_t.FLOP):
                truth_flops.append(output.name)
        # TODO: Detect when values are ready for sending to other nodes

    # Append flop updates not covered by logic
    for flop in partition.tgt_flops:
        # Check if flop has already been handled
        if flop.name in truth_flops:
            continue
        # Locate where the flop should be stored
        tgt_row, tgt_slot, tgt_idx = memory.find(flop)
        # Find the signal driving the flop
        signal = sig_table_map.get(flop.inputs[0], flop.inputs[0])
        if getattr(signal, "type", None) == nxsignal_type_t.CONSTANT:
            # TODO: Generate a constant value and write to memory
            continue
        else:
            stream_iter(emit_source_setup(signal))
            src_reg = next(iter(x for x in registers + [reg_work] if signal in x.elements))
            src_idx = src_reg.elements.index(signal)
            # If bit is not in the right place, swap over
            if tgt_idx != src_idx:
                stream_add(Shuffle(src=src_reg.index,
                                tgt=src_reg.index,
                                mux=[{
                                    src_idx: tgt_idx,
                                    tgt_idx: src_idx
                                }.get(x, x) for x in range(8)]))
                src_reg.elements[tgt_idx], src_reg.elements[src_idx] = (
                    src_reg.elements[src_idx], src_reg.elements[tgt_idx]
                )
            # Write out
            stream_add(Store(src    =src_reg.index,
                             mask   =(1 << tgt_idx),
                             slot   =(tgt_slot // 2),
                             address=tgt_row,
                             offset =Store.offset.PRESERVE))

    # Append a branch to wait for the next trigger
    stream_add(Branch(pc=0,
                      offset=Branch.offset.INVERSE,
                      idle=1,
                      mark=1,
                      comparison=Branch.comparison.WAIT))

    print()

    # Instruction stats
    print("=" * 80)
    print("Instruction Counts:")
    print(f" - Total  : {len(stream):3d}")
    for key, count in counts.items():
        print(f" - {key:7s}: {count:3d}")
    print("=" * 80)
    print()

    # Calculate access deltas
    deltas = {}
    for key, accesses in trk_usage.items():
        deltas[key] = [(y - x) for ((_, x), (_, y)) in zip(accesses, accesses[1:])]
    min_delta = min(sum(deltas.values(), []))
    max_delta = max(sum(deltas.values(), []))
    avg_delta = ceil(mean(sum(deltas.values(), [])))

    # Memory access stats
    write_n_read = set(trk_write.keys()).difference(trk_read.keys())
    read_n_write = set(trk_read.keys()).difference(trk_write.keys())
    sorted_reads = sorted(trk_read.items(), key=lambda x: x[1])
    print("=" * 80)
    print("Memory Accesses:")
    print(f" - Total Writes       : {sum(trk_write.values()):4d}")
    print(f" - Total Reads        : {sum(trk_read.values()):4d}")
    print(f" - Most Read Address  : {sorted_reads[-1][0]} ({sorted_reads[-1][1]} times)")
    print(f" - Written Not Read   : {len(write_n_read):4d}")
    print(f" - Read Not Written   : {len(read_n_write):4d}")
    print(f" - Register Selections: {trk_select:4d}")
    print(f" - Inactive Evictions : {trk_evict_inactive:4d}")
    print(f" - Novel Evictions    : {trk_evict_novel:4d}")
    print(f" - Not Novel Evictions: {trk_evict_notnovel:4d}")
    print(f" - Minimum Residency  : {min_delta:4d}")
    print(f" - Maximum Residency  : {max_delta:4d}")
    print(f" - Average Residency  : {avg_delta:4d}")
    print("=" * 80)
    print()

    return stream

