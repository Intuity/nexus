from dataclasses import dataclass
import math
from typing import Any, Tuple

from nxcompile import nxsignal_type_t
from nxisa import Label, Load, Send, Shuffle, Store, Offset

from py_nxcompile.compiler.messaging import node_to_node
from py_nxcompile.nodecompiler import Node
from py_nxcompile.grouper.grouping import Grouping
from py_nxcompile.grouper.partition import Partition

@dataclass()
class Flop:
    name   : str
    inputs : Tuple[Any] = tuple([])

    def __hash__(self) -> int:
        return hash(self.name)

    def is_type(self, type):
        return type == nxsignal_type_t.FLOP

def test_n2n_no_shuffle(mocker):
    mocker.patch("nxcompile.NXFlop.from_signal", lambda x: x)
    # Create two partitions
    part_a = Partition(0, {}, [], {})
    part_b = Partition(1, {}, [], {})
    # Create some flops
    part_a.tgt_flops = [ (flop_a0 := Flop("flop_a0")),
                         (flop_a1 := Flop("flop_a1")) ]
    part_b.tgt_flops = [ (flop_b0 := Flop("flop_b0")),
                         (flop_b1 := Flop("flop_b1")) ]
    part_a.src_flops = part_b.tgt_flops
    part_b.src_flops = part_a.tgt_flops
    part_a.all_gates = []
    part_b.all_gates = []
    part_a.src_ports = []
    part_b.src_ports = []
    # Cross-link flops
    flop_a0.inputs = (flop_b0, )
    flop_a1.inputs = (flop_b1, )
    flop_b0.inputs = (flop_a0, )
    flop_b1.inputs = (flop_a1, )
    # Create groupings
    part_a.groups = [Grouping(flop_a0, [], [], [flop_b0], []),
                     Grouping(flop_a1, [], [], [flop_b1], [])]
    part_b.groups = [Grouping(flop_b0, [], [], [flop_a0], []),
                     Grouping(flop_b1, [], [], [flop_a1], [])]
    part_a.groups[0].partition = part_a
    part_a.groups[1].partition = part_a
    part_b.groups[0].partition = part_b
    part_b.groups[1].partition = part_b
    part_a.groups[0].driven_by = [part_b.groups[0]]
    part_a.groups[1].driven_by = [part_b.groups[1]]
    part_b.groups[0].driven_by = [part_a.groups[0]]
    part_b.groups[1].driven_by = [part_a.groups[1]]
    # Allocate nodes
    node_a = Node(part_a, 0, 0)
    node_b = Node(part_b, 0, 1)
    # Check that target flops have been placed
    assert flop_a0 in node_a.memory.rows[0].slots[2].elements
    assert flop_a1 in node_a.memory.rows[0].slots[2].elements
    assert flop_a0 in node_a.memory.rows[0].slots[3].elements
    assert flop_a1 in node_a.memory.rows[0].slots[3].elements
    assert flop_b0 in node_b.memory.rows[0].slots[2].elements
    assert flop_b1 in node_b.memory.rows[0].slots[2].elements
    assert flop_b0 in node_b.memory.rows[0].slots[3].elements
    assert flop_b1 in node_b.memory.rows[0].slots[3].elements
    # Check that source flops have been placed (cross-over)
    assert flop_b0 in node_a.memory.rows[0].slots[0].elements
    assert flop_b1 in node_a.memory.rows[0].slots[0].elements
    assert flop_b0 in node_a.memory.rows[0].slots[1].elements
    assert flop_b1 in node_a.memory.rows[0].slots[1].elements
    assert flop_a0 in node_b.memory.rows[0].slots[0].elements
    assert flop_a1 in node_b.memory.rows[0].slots[0].elements
    assert flop_a0 in node_b.memory.rows[0].slots[1].elements
    assert flop_a1 in node_b.memory.rows[0].slots[1].elements
    # Record mapping
    mapping = {
        "flop_a0": [node_b],
        "flop_a1": [node_b],
        "flop_b0": [node_a],
        "flop_b1": [node_a],
    }
    # Compile node-to-node communications
    for src_node, tgt_node, flops in ((node_a, node_b, [flop_a0, flop_a1]),
                                      (node_b, node_a, [flop_b0, flop_b1])):
        seq = list(node_to_node(src_node, mapping))
        assert isinstance(seq[0], Label) and seq[0].label == f"node_{tgt_node.row}_{tgt_node.column}"
        # - First Load/Store
        assert seq[1].instr is Load
        assert seq[1].fields["offset"] == Offset().INVERSE
        slot = src_node.memory.rows[seq[1].fields["address"]]\
                              .slots[seq[1].fields["slot"] << 1]
        assert seq[2].instr is Store
        assert seq[2].fields["src"] == seq[1].fields["tgt"]
        assert seq[2].fields["address"] == 1023
        assert seq[2].fields["slot"] == 0
        assert seq[2].fields["offset"] == Offset().SET_LOW
        local_x = slot.elements[(index_x := int(math.log2(seq[2].fields["mask"])))]
        # - Second Load/Store
        assert seq[3].instr is Load
        assert seq[3].fields["offset"] == Offset().INVERSE
        slot = src_node.memory.rows[seq[3].fields["address"]]\
                              .slots[seq[3].fields["slot"] << 1]
        assert seq[4].instr is Store
        assert seq[4].fields["src"] == seq[3].fields["tgt"]
        assert seq[4].fields["address"] == 1023
        assert seq[4].fields["slot"] == 0
        assert seq[4].fields["offset"] == Offset().SET_LOW
        local_y = slot.elements[(index_y := int(math.log2(seq[4].fields["mask"])))]
        # - Check both A0 & A1 have been picked up
        assert not { local_x, local_y }.symmetric_difference(flops)
        # - Load back from memory
        assert seq[5].instr is Load
        assert seq[5].fields["tgt"] == 0
        assert seq[5].fields["address"] == 1023
        assert seq[5].fields["slot"] == 0
        assert seq[5].fields["offset"] == Offset().SET_LOW
        # - Send to target
        assert seq[6].instr is Send
        assert seq[6].fields["src"] == 0
        assert seq[6].fields["node_row"] == tgt_node.row
        assert seq[6].fields["node_col"] == tgt_node.column
        assert seq[6].fields["offset"] == Offset().INVERSE
        slot = tgt_node.memory.rows[seq[6].fields["address"]]\
                              .slots[seq[6].fields["slot"] << 1]
        assert slot.elements[index_x] is local_x
        assert slot.elements[index_y] is local_y

def test_n2n_shuffle(mocker):
    mocker.patch("nxcompile.NXFlop.from_signal", lambda x: x)
    # Create two partitions
    part_a = Partition(0, {}, [], {})
    part_b = Partition(1, {}, [], {})
    # Create some flops
    part_a.tgt_flops = [ (flop_a0 := Flop("flop_a0")),
                         (flop_a1 := Flop("flop_a1")) ]
    part_b.tgt_flops = [ (flop_b0 := Flop("flop_b0")),
                         (flop_b1 := Flop("flop_b1")) ]
    part_a.src_flops = part_b.tgt_flops
    part_b.src_flops = part_a.tgt_flops
    part_a.all_gates = []
    part_b.all_gates = []
    part_a.src_ports = []
    part_b.src_ports = []
    # Cross-link flops
    flop_a0.inputs = (flop_b1, )
    flop_a1.inputs = (flop_b0, )
    flop_b0.inputs = (flop_a1, )
    flop_b1.inputs = (flop_a0, )
    # Create groupings
    part_a.groups = [Grouping(flop_a0, [], [], [flop_b1], []),
                     Grouping(flop_a1, [], [], [flop_b0], [])]
    part_b.groups = [Grouping(flop_b0, [], [], [flop_a1], []),
                     Grouping(flop_b1, [], [], [flop_a0], [])]
    part_a.groups[0].partition = part_a
    part_a.groups[1].partition = part_a
    part_b.groups[0].partition = part_b
    part_b.groups[1].partition = part_b
    part_a.groups[0].driven_by = [part_b.groups[1]]
    part_a.groups[1].driven_by = [part_b.groups[0]]
    part_b.groups[0].driven_by = [part_a.groups[1]]
    part_b.groups[1].driven_by = [part_a.groups[0]]
    # Allocate nodes
    node_a = Node(part_a, 0, 0)
    node_b = Node(part_b, 0, 1)
    # Check that target flops have been placed
    assert flop_a0 in node_a.memory.rows[0].slots[2].elements
    assert flop_a1 in node_a.memory.rows[0].slots[2].elements
    assert flop_a0 in node_a.memory.rows[0].slots[3].elements
    assert flop_a1 in node_a.memory.rows[0].slots[3].elements
    assert flop_b0 in node_b.memory.rows[0].slots[2].elements
    assert flop_b1 in node_b.memory.rows[0].slots[2].elements
    assert flop_b0 in node_b.memory.rows[0].slots[3].elements
    assert flop_b1 in node_b.memory.rows[0].slots[3].elements
    # Check that source flops have been placed (cross-over)
    assert flop_b0 in node_a.memory.rows[0].slots[0].elements
    assert flop_b1 in node_a.memory.rows[0].slots[0].elements
    assert flop_b0 in node_a.memory.rows[0].slots[1].elements
    assert flop_b1 in node_a.memory.rows[0].slots[1].elements
    assert flop_a0 in node_b.memory.rows[0].slots[0].elements
    assert flop_a1 in node_b.memory.rows[0].slots[0].elements
    assert flop_a0 in node_b.memory.rows[0].slots[1].elements
    assert flop_a1 in node_b.memory.rows[0].slots[1].elements
    # Record mapping
    mapping = {
        "flop_a0": [node_b],
        "flop_a1": [node_b],
        "flop_b0": [node_a],
        "flop_b1": [node_a],
    }
    # Compile node-to-node communications
    for src_node, tgt_node, flops in ((node_a, node_b, [flop_a0, flop_a1]),
                                      (node_b, node_a, [flop_b0, flop_b1])):
        seq = list(node_to_node(src_node, mapping))
        assert isinstance(seq[0], Label) and seq[0].label == f"node_{tgt_node.row}_{tgt_node.column}"
        # First Load/Store
        assert seq[1].instr is Load
        assert seq[1].fields["offset"] == Offset().INVERSE
        slot = src_node.memory.rows[seq[1].fields["address"]]\
                              .slots[seq[1].fields["slot"] << 1]
        assert seq[2].instr is Shuffle
        assert seq[2].fields["src"] == 0
        assert seq[2].fields["tgt"] == 0
        assert seq[2].fields["mux"] == [1, 0, 2, 3, 4, 5, 6, 7]
        assert seq[3].instr is Store
        assert seq[3].fields["src"] == seq[1].fields["tgt"]
        assert seq[3].fields["address"] == 1023
        assert seq[3].fields["slot"] == 0
        assert seq[3].fields["offset"] == Offset().SET_LOW
        local_x = slot.elements[(index_x := int(math.log2(seq[3].fields["mask"])))]
        # Second Load/Store
        assert seq[4].instr is Load
        assert seq[4].fields["offset"] == Offset().INVERSE
        slot = src_node.memory.rows[seq[4].fields["address"]]\
                              .slots[seq[4].fields["slot"] << 1]
        assert seq[5].instr is Shuffle
        assert seq[5].fields["src"] == 0
        assert seq[5].fields["tgt"] == 0
        assert seq[5].fields["mux"] == [1, 0, 2, 3, 4, 5, 6, 7]
        assert seq[6].instr is Store
        assert seq[6].fields["src"] == seq[4].fields["tgt"]
        assert seq[6].fields["address"] == 1023
        assert seq[6].fields["slot"] == 0
        assert seq[6].fields["offset"] == Offset().SET_LOW
        local_y = slot.elements[(index_y := int(math.log2(seq[6].fields["mask"])))]
        # Check both A0 & A1 have been picked up
        assert not { local_x, local_y }.symmetric_difference(flops)
        # Load back from memory
        assert seq[7].instr is Load
        assert seq[7].fields["tgt"] == 0
        assert seq[7].fields["address"] == 1023
        assert seq[7].fields["slot"] == 0
        assert seq[7].fields["offset"] == Offset().SET_LOW
        # Send to target
        assert seq[8].instr is Send
        assert seq[8].fields["src"] == 0
        assert seq[8].fields["node_row"] == tgt_node.row
        assert seq[8].fields["node_col"] == tgt_node.column
        assert seq[8].fields["offset"] == Offset().INVERSE
        slot = tgt_node.memory.rows[seq[8].fields["address"]]\
                              .slots[seq[8].fields["slot"] << 1]
        xmap = { 0: 1, 1: 0, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7 }
        assert slot.elements[xmap[index_x]] is local_x
        assert slot.elements[xmap[index_y]] is local_y

def test_n2n_many(mocker):
    mocker.patch("nxcompile.NXFlop.from_signal", lambda x: x)
    # Create two partitions
    part_a = Partition(0, {}, [], {})
    part_b = Partition(1, {}, [], {})
    # Create some flops
    part_a.tgt_flops = [Flop(f"flop_a{x}") for x in range(16)]
    part_b.tgt_flops = [Flop(f"flop_b{x}") for x in range(16)]
    part_a.src_flops = part_b.tgt_flops
    part_b.src_flops = part_a.tgt_flops
    part_a.all_gates = []
    part_b.all_gates = []
    part_a.src_ports = []
    part_b.src_ports = []
    # Cross-link flops
    part_a.groups = []
    part_b.groups = []
    for tgt, src in zip(part_a.tgt_flops, part_b.tgt_flops[::-1]):
        tgt.inputs = (src, )
        part_a.groups.append(Grouping(tgt, [], [], [src], []))
        part_a.groups[-1].partition = part_a
    for tgt, src in zip(part_b.tgt_flops, part_a.tgt_flops[::-1]):
        tgt.inputs = (src, )
        part_b.groups.append(Grouping(tgt, [], [], [src], []))
        part_b.groups[-1].partition = part_b
    for grp_a, grp_b in zip(part_a.groups, part_b.groups[::-1]):
        grp_a.driven_by = [grp_b]
        grp_b.driven_by = [grp_a]
    # Allocate nodes
    node_a = Node(part_a, 0, 0)
    node_b = Node(part_b, 0, 1)
    # Check that target flops have been placed
    for flop in part_a.tgt_flops[:8]:
        assert flop in node_a.memory.rows[1].slots[0].elements
        assert flop in node_a.memory.rows[1].slots[1].elements
    for flop in part_a.tgt_flops[8:]:
        assert flop in node_a.memory.rows[1].slots[2].elements
        assert flop in node_a.memory.rows[1].slots[3].elements
    for flop in part_b.tgt_flops[:8]:
        assert flop in node_b.memory.rows[1].slots[0].elements
        assert flop in node_b.memory.rows[1].slots[1].elements
    for flop in part_b.tgt_flops[8:]:
        assert flop in node_b.memory.rows[1].slots[2].elements
        assert flop in node_b.memory.rows[1].slots[3].elements
    # Check that source flops have been placed (cross-over)
    for flop in part_b.tgt_flops[::-1][:8]:
        assert flop in node_a.memory.rows[0].slots[0].elements
        assert flop in node_a.memory.rows[0].slots[1].elements
    for flop in part_b.tgt_flops[::-1][8:]:
        assert flop in node_a.memory.rows[0].slots[2].elements
        assert flop in node_a.memory.rows[0].slots[3].elements
    for flop in part_a.tgt_flops[::-1][:8]:
        assert flop in node_b.memory.rows[0].slots[0].elements
        assert flop in node_b.memory.rows[0].slots[1].elements
    for flop in part_a.tgt_flops[::-1][8:]:
        assert flop in node_b.memory.rows[0].slots[2].elements
        assert flop in node_b.memory.rows[0].slots[3].elements
    # Record mapping
    mapping = {}
    mapping.update({ x.name: [node_b] for x in part_a.tgt_flops })
    mapping.update({ x.name: [node_a] for x in part_b.tgt_flops })
    # Compile node-to-node communications
    for src_node, tgt_node, flops in ((node_a, node_b, part_a.tgt_flops),
                                      (node_b, node_a, part_b.tgt_flops)):
        seq = list(node_to_node(src_node, mapping))
        assert isinstance(lbl := seq.pop(0), Label) and lbl.label == f"node_{tgt_node.row}_{tgt_node.column}"

        scoreboard = flops[:]
        for _s in range(2):
            # Check each pick and place sequence
            tgt_slot = set()
            for _b in range(8):
                load, shfl, stor = (seq.pop(0) for _ in range(3))
                assert load.instr is Load
                assert shfl.instr is Shuffle
                assert stor.instr is Store
                slot = src_node.memory.rows[load.fields["address"]]\
                                      .slots[load.fields["slot"] << 1]
                src_idx = shfl.fields["mux"][int(math.log2(stor.fields["mask"]))]
                flop = slot.elements[src_idx]
                assert flop in scoreboard
                scoreboard.remove(flop)
                tgt_idx = (tgt_node.memory.rows[0].slots[0].elements +
                           tgt_node.memory.rows[0].slots[2].elements).index(flop)
                assert shfl.fields["mux"][tgt_idx % 8] == src_idx
                assert stor.fields["mask"] == (1 << (tgt_idx % 8))
                tgt_slot.add(tgt_idx // 8)
            # Check exactly one slot is being targeted by the send
            assert len(tgt_slot) == 1
            # Check the send operation
            load, send = (seq.pop(0) for _ in range(2))
            assert load.instr is Load
            assert send.instr is Send
            assert send.fields["node_row"] == tgt_node.row
            assert send.fields["node_col"] == tgt_node.column
            assert send.fields["address"]  == 0
            assert send.fields["offset"]   == Offset().INVERSE
            assert send.fields["slot"]     == list(tgt_slot)[0]
