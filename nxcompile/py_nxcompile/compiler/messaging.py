from collections import defaultdict
from typing import Any, Dict, Iterable

from nxisa import Instance, Load, Shuffle, Store, Send, Label

def node_to_node(node    : Any,
                 mapping : Dict[str, Any]) -> Iterable[Instance]:
    # Assess which flop state needs to be sent to which nodes
    to_send = defaultdict(list)
    for flop in node.partition.tgt_flops:
        for target in mapping.get(flop.name, []):
            # Skip over this node if it appears
            if target is node:
                continue
            # Accumulate based on node
            to_send[target].append(flop)

    # For each node, form messages
    for target, flops in to_send.items():
        # Group flops together into messages based on the target's memory layout
        msgs = defaultdict(lambda: [None] * 8)
        for flop in flops:
            row, slot, bit = target.memory.find(flop)
            msgs[(row, slot)][bit] = flop
        # For each required message
        yield Label(f"node_{target.row}_{target.column}")
        for (t_address, t_slot), req in msgs.items():
            # Group together bits to load from local memory
            load_from = defaultdict(list)
            for t_bit, flop in enumerate(req):
                if flop is None:
                    continue
                l_row, l_slot, l_bit = node.memory.find(flop)
                load_from[l_row, l_slot].append((l_bit, t_bit, flop))
            # Accumulate all of the required state
            for (l_row, l_slot), selection in load_from.items():
                # Load bits
                yield Load(tgt    =0,
                           slot   =(l_slot // 2),
                           address=l_row,
                           offset =Load.offset.INVERSE,
                           comment=f"Load flops {', '.join(f.name for _, _, f in selection)}")
                # Check if bit rearrangement is required
                mapping = { t: l for l, t, _ in selection }
                if any((l != t) for l, t, _ in selection):
                    yield Shuffle(src    = 0,
                                  tgt    = 0,
                                  mux    =[mapping.get(x, x) for x in range(8)],
                                  comment=f"Apply bit mapping {mapping}")
                # Accumulate
                yield Store(src    =0,
                            mask   =sum((1 << t) for _, t, _ in selection),
                            slot   =0,
                            address=1023,
                            offset =Store.offset.SET_LOW,
                            comment="Accumulate flops")
            # Send the message
            yield Load(tgt    =0,
                        slot   =0,
                        address=1023,
                        offset =Load.offset.SET_LOW,
                        comment="Load accumulated state")
            yield Send(src     =0,
                       node_row=target.row,
                       node_col=target.column,
                       slot    =(t_slot // 2),
                       address =t_address,
                       offset  =Send.offset.INVERSE,
                       trig    =0,
                       comment=f"Send to node {target.position}")
