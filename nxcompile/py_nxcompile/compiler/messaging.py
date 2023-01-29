# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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
from typing import Any, Dict, Iterable

from nxisa import Instance, Load, Shuffle, Store, Send, Label, Pick

def node_to_node(node    : Any,
                 mapping : Dict[str, Any]) -> Iterable[Instance]:
    # Allocate memory to accumulate messages
    next_ptr = 127, 1
    def allocate():
        nonlocal next_ptr
        curr_row, curr_slot = next_ptr
        next_ptr = (curr_row - 1, 1) if curr_slot == 0 else (curr_row, curr_slot - 1)
        return curr_row, curr_slot
    pointers = defaultdict(allocate)
    selections = defaultdict(lambda: defaultdict(list))
    for flop in node.partition.tgt_flops:
        for target in filter(lambda x: x is not node, mapping.get(flop.name, [])):
            # Find where the target receives this state
            t_row, t_slot, t_bit = target.memory.find(flop)
            # Find where the local node maintains this state
            l_row, l_slot, l_bit = node.memory.find(flop)
            # Allocate a memory slot for accumulating the message
            a_row, a_slot = pointers[target.row, target.column, t_row, t_slot]
            # Gather data to accumulate from each row of the memory
            selections[l_row, l_slot][a_row, a_slot].append((l_bit, t_bit))

    # Accumulate messages
    yield Label("msg_accum")
    for (l_row, l_slot), targets in selections.items():
        # Load data from memory
        yield Load(tgt    =0,
                   address=l_row,
                   slot   =Load.slot.INVERSE,
                   comment=f"Load data from 0x{l_row:x} slot {l_slot}")
        # For each target, perform pick or shuffle+store
        for (a_row, a_slot), bits in targets.items():
            mapping = { t: l for l, t in bits }
            pick_lsb = not set(mapping.keys()).difference({0,1,2,3})
            pick_msb = not set(mapping.keys()).difference({4,5,6,7})
            if pick_lsb:
                mask = sum((1 << x) for x in mapping.keys())
                yield Pick(src        =0,
                           address_6_0=(a_row % 64),
                           slot       =[Pick.slot.LOWER, Pick.slot.UPPER][a_slot],
                           upper      =0,
                           mux        =[mapping.get(x, 0) for x in range(4)],
                           mask       =mask)
            elif pick_msb:
                mask = sum((1 << x) for x in mapping.keys())
                yield Pick(src        =0,
                           address_6_0=(a_row % 64),
                           slot       =[Pick.slot.LOWER, Pick.slot.UPPER][a_slot],
                           upper      =1,
                           mux        =[mapping.get(x, 0) for x in range(4, 8)],
                           mask       =mask)
            else:
                needs_shuffle = any((l != t) for l, t in bits)
                if needs_shuffle:
                    mapping = { t: l for l, t in bits }
                    yield Shuffle(src    =0,
                                  tgt    =1,
                                  mux    =[mapping.get(x, x) for x in range(8)],
                                  comment=f"Apply bit mapping {mapping}")
                yield Store(src    =[0, 1][needs_shuffle],
                            mask   =sum((1 << t) for _, t in bits),
                            address=a_row,
                            slot   =[Store.slot.LOWER, Store.slot.UPPER][a_slot],
                            comment="Accumulate data")

    # Send accumulated messages
    for (node_row, node_col, t_row, t_slot), (a_row, a_slot) in pointers.items():
        yield Label(f"node_{node_row}_{node_col}_{t_row}_{t_slot}")
        yield Load(tgt    =0,
                   address=a_row,
                   slot   =[Load.slot.LOWER, Load.slot.UPPER][a_slot],
                   comment="Load accumulated state")
        yield Send(src    =0,
                   row    =node_row,
                   column =node_col,
                   address=t_row,
                   slot   =Send.slot.INVERSE,
                   comment=f"Send to node {node_row}, {node_col}")
