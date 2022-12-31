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
from dis import Instruction
from functools import lru_cache
from math import ceil
from statistics import mean
from typing import Dict, Union

from natsort import natsorted
from orderedset import OrderedSet

from nxcompile import nxsignal_type_t, NXGate, NXFlop, NXPort
from nxisa import Load, Store, Branch, Send, Truth, Shuffle, Instance, Label

from .compiler.memory import Memory
from .compiler.messaging import node_to_node
from .compiler.operation import Operation
from .compiler.register import Register
from .compiler.table import Table

class Node:

    def __init__(self, partition, row, column):
        self.partition = partition
        self.row       = row
        self.column    = column
        # Announce
        print(f"Compiling partition {self.partition.id}")
        print(f" - Has {len(self.partition.all_gates)} gates")
        print(f" - Has {len(self.partition.tgt_flops)} flops")
        print()
        # Create a memory
        self.memory = Memory()
        # Identify all of the required logic tables
        self.tables, self.references = self.identify_operations()
        # Assign input, output, and flops to slots in the memory
        self.num_input_slots = self.assign_inputs()
        self.flop_slots, self.flop_cycles, self.flop_targets = self.assign_flops()
        self.output_slots = self.assign_outputs()
        # Debug
        print("Slot Allocation:")
        print(f" - Requires {self.num_input_slots:3d} input slots")
        print(f" - Requires {len(self.flop_slots):3d} flop slots")
        print(f" - Requires {len(self.output_slots):3d} output slots")
        print()
        print("Logic Tables:")
        print(f" - Compiled {len(self.tables):3d} tables")
        print(f" - Referred {sum(map(len, self.references.values())):3d} times")
        print()

    @property
    def position(self):
        return self.row, self.column

    def assign_inputs(self):
        # Accumulate inputs based on source partition
        # NOTE: Excludes signals from own partition
        inputs = defaultdict(OrderedSet)
        for group in self.partition.groups:
            for source in group.driven_by:
                if source.partition.id != self.partition.id:
                    inputs[source.partition.id].add(source.target)
        # Also include inputs coming from external ports
        inputs["EXT"] = self.partition.src_ports
        # Assign inputs to slots in the memory
        num_slots = 0
        for signals in filter(lambda x: len(x) > 0, map(list, inputs.values())):
            for offset in range(0, len(signals), 8):
                # TODO: Cope with combinatorial sources
                self.memory.place_all(signals[offset:offset+8], True)
                num_slots += 1
            # Bump to avoid mixing signals from different source partitions
            self.memory.bump_slot()
        # Bump and align to make next placement safe
        if self.memory.last_bit != 0:
            self.memory.bump_slot()
        self.memory.align(True)
        return num_slots

    def assign_flops(self):
        # Pack results as efficiently as possible
        slots  = []
        cycles = {}
        # Consider table results in chunks of 8
        for idx in range(0, len(self.tables), 8):
            # Take chunk & reverse it (as results are shifted up the register)
            chunk = self.tables[idx:idx+8][::-1]
            # Work out which results drive flops
            for cix, entry in enumerate(chunk):
                flops = [x for x in entry.op.gate.outputs if x.is_type(nxsignal_type_t.FLOP)]
                if flops:
                    # TODO: Turn this check back on!
                    # assert len(flops) == 1
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
        for flop in self.partition.tgt_flops:
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
                slots[-1][0] = flop
        # Allocate slots in the memory
        # NOTE: Don't use Memory.place_all as that will tightly pack bits to the LSB
        targets = []
        for slot in slots:
            # If bit cursor is not 0, bounce to next slot
            if self.memory.last_bit != 0:
                self.memory.bump_slot()
            # Ensure that the slot is sequentially aligned
            self.memory.align(is_seq=True)
            targets.append((self.memory.last_row, self.memory.last_slot))
            # Mark slot as sequential
            self.memory.slot.is_seq = True
            # Fill in the memory elements
            for idx, elem in enumerate(slot):
                self.memory.slot.elements[idx] = elem
                self.memory.next_slot.elements[idx] = elem
                if elem is not None:
                    self.memory.mapping[elem.name] = (self.memory.last_row, self.memory.last_slot, idx)
            # Stop this slot being modified
            self.memory.bump_slot()
        # Return the slots and cycle encodings
        return slots, cycles, targets

    def assign_outputs(self):
        # Accumulate outputs based on target partition
        outputs = defaultdict(OrderedSet)
        for group in self.partition.groups:
            for target in group.drives_to:
                if target.partition.id != self.partition.id:
                    outputs[target.partition.id].add(target.target)
        # Assign outputs to slots
        output_slots = []
        for signals in map(list, outputs.values()):
            for offset in range(0, len(signals), 8):
                chunk  = signals[offset:offset+8]
                chunk += [None] * (8 - len(chunk))
                output_slots.append(chunk)
        return output_slots

    def identify_operations(self):
        # Wrap every gate in an operation
        ops = {}
        for gate in self.partition.all_gates:
            ops[gate.name] = Operation(NXGate.from_signal(gate))

        @lru_cache
        def chase(signal, flag_constants=True):
            if signal.is_type(nxsignal_type_t.WIRE):
                return chase(signal.inputs[0])
            elif signal.is_type(nxsignal_type_t.GATE):
                return ops[signal.name]
            elif signal.is_type(nxsignal_type_t.FLOP):
                return NXFlop.from_signal(signal)
            elif signal.is_type(nxsignal_type_t.PORT):
                return NXPort.from_signal(signal)
            elif signal.is_type(nxsignal_type_t.CONSTANT):
                if flag_constants:
                    raise Exception("Unoptimised constant term found!")
            else:
                raise Exception(f"UNKNOWN TYPE: {signal.type}")

        # Link operations together & track direct references
        refs = defaultdict(list)
        for op in ops.values():
            for input in op.gate.inputs:
                op.inputs.append(found := chase(input))
                if isinstance(found, Operation):
                    refs[found.gate.name].append(op)

        # Include references from flops
        for flop in self.partition.tgt_flops:
            driver = chase(flop.inputs[0], flag_constants=False)
            if isinstance(driver, Operation):
                refs[driver.gate.name].append(flop)

        # Order operations by number of references
        ordered = [ops[x[0]] for x in sorted(refs.items(), key=lambda x: len(x[1]), reverse=True)]

        # Compile truth tables for all operations
        tables = {}
        for op in ordered:
            # Attempt to merge supporting operations
            current  = op.inputs
            contrib  = []
            best_ins = current[:]
            best_ops = []
            while True:
                # Track successful expansions
                expanded = False
                # Iterate through each term in the current expression
                work_ins = []
                work_ops = contrib[:]
                for idx_term, term in enumerate(current):
                    # Reuse existing tables
                    if term in tables:
                        work_ins.append(tables[term])
                    # Expand operations which haven't been previously converted
                    elif isinstance(term, Operation):
                        work_ins += term.inputs
                        work_ops.append(term)
                        expanded = True
                    # Anything else append as a direct input
                    else:
                        work_ins.append(term)
                    # Join with the remainder
                    full_ins = work_ins + current[idx_term+1:]
                    if len(set(full_ins)) <= 3:
                        best_ins = list(OrderedSet(full_ins))
                        best_ops = work_ops[:]
                # Update the current state
                current = work_ins[:]
                contrib = work_ops[:]
                # If no expansion occurred, stop searching
                if not expanded:
                    break
            # Iterate through the input combinations and evaluate the function
            result = []
            for idx in range(1 << len(best_ins)):
                values = {}
                for shift, input in enumerate(best_ins):
                    values[input.op if isinstance(input, Table) else input] = ((idx >> shift) & 1)
                result.append(op.evaluate(values))
            # Expand result to fill all 8 slots
            result = (8 // len(result)) * result
            # Create a table
            tables[op] = Table(op, best_ins, result, [op] + best_ops)

        # Update any table inputs to reference other tables
        for table in tables.values():
            for idx, input in enumerate(table.inputs):
                if isinstance(input, Operation):
                    table.inputs[idx] = tables[input]

        # Eliminate truth tables which are not referenced
        print(f"Compiled {len(tables)} tables")
        while True:
            # Freshly count references
            refs = defaultdict(lambda: 0)
            for table in tables.values():
                for input in table.inputs:
                    if isinstance(input, Table):
                        refs[input.op.gate.name] += 1
            for flop in self.partition.tgt_flops:
                refs[flop.inputs[0].name] += 1
            # Drop any items with a zero count
            dropped = 0
            for op in list(tables.keys()):
                if refs[op.gate.name] == 0:
                    del tables[op]
                    dropped += 1
            # If no terms dropped, break out
            print(f"Dropped {dropped} tables")
            if dropped == 0:
                break
        print(f"There are {len(tables)} remaining tables")

        # Sum all included operations
        all_ins = []
        all_ops = []
        all_tgt = []
        for table in tables.values():
            all_ins += [x for x in table.inputs if not isinstance(x, (Table, Operation))]
            all_ops += table.ops
            all_tgt += [x for x in table.op.gate.outputs if x.is_type(nxsignal_type_t.FLOP)]

        # Count number of simple and complex ops
        simple_ops  = 0
        complex_ops = 0
        for table in tables.values():
            if len(table.ops) == 1 and len(table.inputs) <= 2:
                simple_ops += 1
            else:
                complex_ops += 1

        print(f"All Inputs : {len(set(all_ins))}")
        print(f"All Ops    : {len(set(all_ops))}")
        print(f"All Tgts   : {len(set(all_tgt))}")
        print(f"Simple Ops : {simple_ops}")
        print(f"Complex Ops: {complex_ops}")

        # Convert tables to a list
        tables = list(tables.values())

        # Build table-to-table references
        refs = defaultdict(OrderedSet)
        for table in tables:
            # Track tables using other tables as inputs
            for input in table.inputs:
                if isinstance(input, Table):
                    refs[input].add(table)
            # Track flops consuming a table's output
            for signal in table.op.gate.outputs:
                if signal.name in (x.name for x in self.partition.tgt_flops):
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

        return satisfied, refs

    def compile(self, send_targets : Dict[str, "Node"], port_offset : int):
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

        def select_register(op_idx, exclude=None):
            nonlocal registers, trk_select, trk_evict_inactive, trk_evict_novel, trk_evict_notnovel
            # Setup & tracking
            exclude     = exclude or []
            trk_select += 1
            # Filter out non-excluded registers
            legal = list(filter(lambda x: (x not in exclude), registers))
            # If there are any inactive registers, choose one of those first
            if inactive := [x for x in legal if not x.active]:
                trk_evict_inactive += 1
                return inactive[0]
            # For each register, analyse the proximity of the next use
            proximities = []
            for reg in legal:
                proximity = len(self.tables)
                for elem in reg.elements:
                    if elem is None:
                        continue
                    for idx, op in enumerate(self.tables[op_idx:]):
                        if elem.name in (x.name for x in op.inputs if x is not None):
                            proximity = min(proximity, idx)
                            break
                proximities.append((proximity, reg))
            # Sort registers by descending proximity & pick item 0 (furthest away)
            _, chosen = sorted(proximities, key=lambda x: x[0], reverse=True)[0]
            # Track if register holds 'novel' values (requires a store)
            if chosen.novel:
                trk_evict_novel += 1
            else:
                trk_evict_notnovel += 1
            return chosen

        def emit_register_reuse(register):
            nonlocal trk_write
            if register.active and register.novel:
                # Find any elements which are combinational and are required later
                to_keep = [None] * 8
                for idx, elem in enumerate(register.elements):
                    if isinstance(elem, Table) and len(self.references.get(elem, [])) > 0:
                        to_keep[idx] = elem
                # Store to memory
                # TODO: This could be optimised a lot to pack evicted registers into
                #       already existing entries
                if any(to_keep):
                    self.memory.bump_slot()
                    row, slot = self.memory.last_row, self.memory.last_slot
                    for idx, elem in enumerate(to_keep):
                        if elem is not None:
                            self.memory.slot.elements[idx] = elem
                            self.memory.mapping[elem.name] = row, slot, idx
                    yield Store(src    =register.index,
                                mask   =0xFF,
                                slot   =(slot // 2),
                                address=row,
                                offset =(2 | (slot % 2)))
            register.activate()
            register.age   = 0
            register.novel = False

        def emit_source_setup(op_idx, signal, exclude=None):
            nonlocal registers, trk_read
            exclude = exclude or []
            # Search for this signal in the registers
            for reg in registers + [reg_work]:
                if signal.name in (x.name for x in reg.elements if x is not None):
                    break
            # If not found, then try to load in from memory
            else:
                tgt = select_register(op_idx, exclude)
                yield from emit_register_reuse(tgt)
                # Search in memory
                if mapping := self.memory.find(signal):
                    row, slot, _ = mapping
                    # For combinational logic, force offset high or low based on slot
                    if isinstance(signal, Table):
                        offset_mode = 2 | (slot % 2)
                    # For sequential mode, use the current offset state (preserve)
                    else:
                        offset_mode = Load.offset.PRESERVE
                    # Emit load
                    elements = self.memory.rows[row].slots[slot].elements
                    yield Load(tgt    =tgt.index,
                               slot   =(slot // 2),
                               address=row,
                               offset =offset_mode,
                               comment=f"Loading R{tgt.index} with {', '.join((x.name if x else '-') for x in elements)}")
                    trk_usage[(row, slot)].append(("read", len(stream)))
                    trk_read[(row, slot)] += 1
                    tgt.elements = elements[:]
                else:
                    # Not found
                    raise Exception(f"Failed to locate signal '{signal}'")

        emitted_flop_cycles = []
        def emit_flush(cone_idx, exclude=None):
            # Move value out to a target register (uses shuffle but keeps order)
            tgt = select_register(cone_idx, exclude=exclude)
            yield from emit_register_reuse(tgt)
            yield Shuffle(src=reg_work.index,
                          tgt=tgt.index,
                          mux=list(range(8)),
                          comment=f"Copy {reg_work.index} to {tgt.index}")
            tgt.elements      = reg_work.elements[:]
            tgt.novel         = True
            reg_work.elements = [None] * 8
            # If this is corresponds to a flop update, perform masked store
            if (selection := self.flop_cycles.get(cone_idx, None)):
                emitted_flop_cycles.append(cone_idx)
                slot_idx, places = selection
                row, slot        = self.flop_targets[slot_idx]
                names            = [self.memory.rows[row].slots[slot].elements[x].name for x in places]
                yield Store(src    =reg_work.index,
                            mask   =sum(((1 << x) for x in places)),
                            slot   =(slot // 2),
                            address=row,
                            offset =Store.offset.INVERSE,
                            comment=f"Flushing out {', '.join(names)}")

        def emit_operation(cone_idx, cone):
            nonlocal registers
            # Gather inputs
            srcs = []
            idxs = []
            for input in cone.inputs:
                yield from emit_source_setup(cone_idx, input, exclude=srcs)
                for reg in registers + [reg_work]:
                    if input.name in (getattr(x, "name", None) for x in reg.elements):
                        srcs.append(reg)
                        idxs.append([getattr(x, "name", None) for x in reg.elements].index(input.name))
                        break
                else:
                    raise Exception("Failed to locate input")
                if isinstance(input, Table) and input in self.references and cone in self.references[input]:
                    self.references[input].remove(cone)
            # Check if working register has reached a flush point (all registers full)
            if None not in reg_work.elements:
                yield from emit_flush(cone_idx, exclude=srcs)
            # Extract and pad the lookup table
            table = 0
            srcs  = [x.index for x in srcs] + ([0] * (3 - len(srcs)))
            table = sum([(x << i) for i, x in enumerate(cone.outputs)])
            assert table >= 0 and table <= 0xFF, "Incorrect table value"
            # Emit an instruction
            yield Truth(src=srcs,
                        mux=idxs,
                        table=table,
                        comment=cone.name + " - " +
                                cone.op.render(include=[cone.op] + cone.inputs) +
                                " - " + ", ".join([x.name for x in cone.inputs]))
            # Shift working register and insert new value
            reg_work.elements = [cone] + reg_work.elements[:7]

        # Assemble the computation stream
        counts = defaultdict(lambda: 0)
        print("Generating Instruction Stream:")
        print()
        def stream_add(instr : Union[Instruction, Label]):
            stream.append(instr)
            if isinstance(instr, Instance):
                counts[instr.instr.opcode.op_name] += 1
                print(f"[{len(stream):04d}] {instr.to_asm():40} -> 0x{instr.encode():08X}")

        def stream_iter(gen):
            for instr in gen:
                stream_add(instr)
                for reg in registers:
                    reg.aging()

        truth_flops = []
        stream_add(Label("compute"))
        for idx, table in enumerate(self.tables):
            stream_iter(emit_operation(idx, table))
            for output in table.op.gate.outputs:
                if output.is_type(nxsignal_type_t.FLOP):
                    truth_flops.append(output.name)
            # TODO: Detect when values are ready for sending to other nodes

        # Flush any flop state left in work register
        stream_add(Label("flush"))
        for index in self.flop_cycles.keys():
            if index not in emitted_flop_cycles:
                stream_iter(emit_flush(index))

        # Append flop updates not covered by logic
        stream_add(Label("pipeline"))
        for flop in self.partition.tgt_flops:
            # Check if flop has already been handled
            if flop.name in truth_flops:
                continue
            # Locate where the flop should be stored
            tgt_row, tgt_slot, tgt_idx = self.memory.find(flop)
            # Find the signal driving the flop
            signal = flop.inputs[0]
            if getattr(signal, "type", None) == nxsignal_type_t.CONSTANT:
                # TODO: Generate a constant value and write to memory
                continue
            else:
                # Locate the signal in registers or memory
                stream_iter(emit_source_setup(len(stream), signal))
                for reg in registers + [reg_work]:
                    if signal.name in (getattr(x, "name", None) for x in reg.elements):
                        src_reg = reg
                        src_idx = [getattr(x, "name", None) for x in reg.elements].index(signal.name)
                        break
                else:
                    raise Exception(f"Failed to find {signal.name}")
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
                                offset =Store.offset.INVERSE))

        print()
        print("# Inserting port state updates")
        print()

        # Pack ports into chunks of 8
        port_mapping = []
        for port in natsorted(self.partition.tgt_ports, key=lambda x: x.name):
            if len(port_mapping) == 0 or len(port_mapping[-1]) >= 8:
                port_mapping.append([])
            port_mapping[-1].append((port, port.inputs[0]))

        # Build operations to expose port states
        stream_add(Label("ports"))
        for idx_map, mapping in enumerate(port_mapping):
            # # Find any signals currently in registers
            # locations = []
            # for _, signal in mapping:
            #     for idx_reg, reg in enumerate(registers + [reg_work]):
            #         for idx_elem, elem in enumerate(reg.elements):
            #             if signal.name == getattr(elem, "name", None):
            #                 locations.append((idx_reg, idx_elem))
            #                 break
            #         else:
            #             continue
            #         break
            #     else:
            #         locations.append(None)
            # # If any signals were found, accumulate them
            # if any((x for x in locations if x is not None)):
            #     print("Found some signals in registers")
            #     # TODO: Do something!
            # Now search for remaining signals in memory
            mem_locs = defaultdict(dict)
            for idx, (_, signal) in enumerate(mapping):
                # # Skip entries which have already been found
                # if location is not None:
                #     continue
                # Locate in the memory
                row, slot, bit = self.memory.find(signal)
                mem_locs[(row, slot)][idx] = bit
            # For each memory location
            for (row, slot), entries in mem_locs.items():
                # Load from the memory location
                stream_add(Load(tgt    =0,
                                slot   =(slot // 2),
                                address=row,
                                # TODO: Is this right?
                                offset =Load.offset.INVERSE))
                # Shuffle bits to match expected order
                stream_add(Shuffle(src=0,
                                   tgt=0,
                                   mux=[entries.get(x, 0) for x in range(8)]))
                # Accumulate using memory masking
                stream_add(Store(src    =0,
                                 mask   =sum((1 << x) for x in entries.keys()),
                                 slot   =0,
                                 address=1023,
                                 offset =Store.offset.SET_LOW))
            # Read back the value and send it
            stream_add(Load(tgt    =0,
                            slot   =0,
                            address=1023,
                            offset =Store.offset.SET_LOW))
            stream_add(Send(src     =0,
                            node_row=15,
                            node_col=0,
                            slot    =0,
                            address =port_offset + idx_map,
                            offset  =0,
                            trig    =0))

        print()
        print("# Inserting node-to-node updates")
        print()

        for op in node_to_node(self, send_targets):
            stream_add(op)

        # Append a branch to wait for the next trigger
        print()
        print("# Inserting loop point")
        print()
        stream_add(Label("loop"))
        stream_add(Branch(pc=0,
                        offset=Branch.offset.INVERSE,
                        idle=1,
                        mark=1,
                        comparison=Branch.comparison.WAIT))

        # Instruction stats
        print()
        print("=" * 80)
        print("Instruction Counts:")
        print(f" - Total  : {len(stream):3d}")
        for key, count in counts.items():
            print(f" - {key:7s}: {count:3d}")
        print("=" * 80)
        print()

        rendered = {}
        for table in self.tables:
            sub_ops = [x.op for x in table.inputs if isinstance(x, Table)]
            rendered[table.op.gate.name] = table.op.render(include=[table.op] + sub_ops)

        # Calculate access deltas
        deltas = {}
        for key, accesses in trk_usage.items():
            deltas[key] = [(y - x) for ((_, x), (_, y)) in zip(accesses, accesses[1:])]
        min_delta, max_delta, avg_delta = 0, 0, 0
        all_deltas = sum(deltas.values(), [])
        if len(all_deltas) > 0:
            min_delta = min(all_deltas)
            max_delta = max(all_deltas)
            avg_delta = ceil(mean(all_deltas))

        # Memory access stats
        write_n_read = OrderedSet(trk_write.keys()).difference(trk_read.keys())
        read_n_write = OrderedSet(trk_read.keys()).difference(trk_write.keys())
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

        # Dump memory mappings
        mem_map = defaultdict(lambda: defaultdict(dict))
        for idx_row, row in enumerate(self.memory.rows):
            for idx_slot, slot in enumerate(row.slots):
                mem_map[idx_row][idx_slot] = [(x.name if x is not None else None) for x in slot.elements]

        return stream, port_mapping, mem_map
