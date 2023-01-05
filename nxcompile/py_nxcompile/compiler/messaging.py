from collections import defaultdict
from typing import Any, Dict, Iterable

from nxisa import Instance, Load, Shuffle, Store, Send, Label, Pick

def node_to_node(node    : Any,
                 mapping : Dict[str, Any]) -> Iterable[Instance]:
    # Allocate memory to accumulate messages
    next_ptr = 127, 3
    def allocate():
        nonlocal next_ptr
        curr_row, curr_slot = next_ptr
        next_ptr = (curr_row - 1, 3) if curr_slot == 0 else (curr_row, curr_slot - 1)
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
                   slot   =(l_slot // 2),
                   address=l_row,
                   offset =Load.offset.INVERSE,
                   comment=f"Load data from 0x{l_row:x} slot {l_slot}")
        # For each target, perform pick or shuffle+store
        for (a_row, a_slot), bits in targets.items():
            mapping = { t: l for l, t in bits }
            pick_lsb = not set(mapping.keys()).difference({0,1,2,3})
            pick_msb = not set(mapping.keys()).difference({4,5,6,7})
            if pick_lsb:
                mask = sum((1 << x) for x in mapping.keys())
                yield Pick(src          =0,
                           short_address=(a_row % 64),
                           slot         =(a_slot // 2),
                           offset       =[Store.offset.SET_LOW, Store.offset.SET_HIGH][a_slot % 2],
                           upper        =0,
                           p0           =mapping.get(0, 0),
                           p1           =mapping.get(1, 0),
                           p2_0         =(mapping.get(2, 0) & 0x1),
                           p2_2_1       =((mapping.get(2, 0) >> 1) & 0x3),
                           p3           =mapping.get(3, 0),
                           mask_2_0     =(mask & 0x7),
                           mask_3       =((mask >> 3) & 0x1))
            elif pick_msb:
                mask = sum((1 << x) for x in mapping.keys())
                yield Pick(src          =0,
                           short_address=(a_row % 64),
                           slot         =(a_slot // 2),
                           offset       =[Store.offset.SET_LOW, Store.offset.SET_HIGH][a_slot % 2],
                           upper        =1,
                           p0           =mapping.get(4, 0),
                           p1           =mapping.get(5, 0),
                           p2_0         =(mapping.get(6, 0) & 0x1),
                           p2_2_1       =((mapping.get(6, 0) >> 1) & 0x3),
                           p3           =mapping.get(7, 0),
                           mask_2_0     =((mask >> 4) & 0x7),
                           mask_3       =((mask >> 7) & 0x1))
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
                            slot   =(a_slot // 2),
                            address=a_row,
                            offset =[Store.offset.SET_LOW, Store.offset.SET_HIGH][a_slot % 2],
                            comment="Accumulate data")

    # Send accumulated messages
    for (node_row, node_col, t_row, t_slot), (a_row, a_slot) in pointers.items():
        yield Label(f"node_{node_row}_{node_col}_{t_row}_{t_slot}")
        yield Load(tgt    =0,
                   address=a_row,
                   slot   =(a_slot // 2),
                   offset =[Store.offset.SET_LOW, Store.offset.SET_HIGH][(a_slot % 2)],
                   comment="Load accumulated state")
        yield Send(src     =0,
                   node_row=node_row,
                   node_col=node_col,
                   address =t_row,
                   slot    =(t_slot // 2),
                   offset  =Send.offset.INVERSE,
                   trig    =0,
                   comment=f"Send to node {node_row}, {node_col}")
