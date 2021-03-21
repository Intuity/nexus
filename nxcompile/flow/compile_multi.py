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

import logging
from statistics import mean

from ..models.flop import Flop
from ..models.gate import Gate, Operation
from ..models.port import PortBit

log = logging.getLogger("compiler.compile")

class Input:
    """ Represents a boundary input or flop output within the logic """
    def __init__(self, bit, targets):
        self.bit     = bit
        self.targets = targets

    def __repr__(self): return f"<Input {self.bit}>"

    @property
    def is_flop(self): return isinstance(self.bit.port.parent, Flop)

class Output:
    """ Represents a boundary output from the logic """
    def __init__(self, bit, source):
        self.bit    = bit
        self.source = source

    def __repr__(self): return f"<Output {self.bit}>"

class Register:
    """ Temporary registering of a result between instructions within a node """
    def __repr__(self): return "<Register>"

class Wire:
    """ Combinatorial connectivity between two different nodes """
    ID = 0
    def __init__(self, keep=False):
        self.id       = Wire.ID
        self.keep     = keep
        self.driver   = None
        self.targets  = []
        Wire.ID      += 1
    def __repr__(self): return f"<Wire {self.id}>"

class Instruction:

    def __init__(self, sig, op, sources, targets, node):
        self.sig     = sig
        self.op      = op
        self.sources = sources
        self.targets = targets
        self.node    = node

    @property
    def inputs(self):
        """ Return a list of sources that require input slots on a node """
        return [x for x in self.sources if type(x) in (Input, Wire)]

    @property
    def outputs(self):
        """ Return a list of targets that require output slots on a node """
        return [x for x in self.targets if type(x) in (Output, Wire)]

    @property
    def target_registers(self):
        """ Return a list of targets that require registers (intra-node) """
        return [x for x in self.targets if isinstance(x, Register)]

    @property
    def target_wires(self):
        """ Return a list of targets that require wires (inter-node) """
        return [x for x in self.targets if isinstance(x, Wire)]

class Node:

    def __init__(
        self, row, column, inputs=8, outputs=8, slots=32, registers=8
    ):
        # Position within the mesh
        self.position = (row, column)
        # Keep a record of available resources
        self.__num_inputs    = inputs
        self.__num_outputs   = outputs
        self.__num_slots     = slots
        self.__num_registers = registers
        # Keep track of how many of each type of resource is consumed
        self.__used_inputs    = []
        self.__used_outputs   = []
        self.__used_registers = []
        # Keep a list of all operations
        self.__ops = []

    @property
    def ops(self):
        return self.__ops[:]

    @property
    def input_usage(self): return (len(self.__used_inputs) / self.__num_inputs)
    @property
    def output_usage(self): return (len(self.__used_outputs) / self.__num_outputs)
    @property
    def slot_usage(self): return (len(self.__ops) / self.__num_slots)

    @property
    def usage(self):
        return max(self.input_usage, self.output_usage, self.slot_usage)

    @property
    def capacity(self):
        return 1 - self.usage

    def add_op(self, op):
        assert not self.contains_op(op)
        assert op.node == None
        # Attach operation to node
        self.__ops.append(op)
        op.node = self
        # Update counts for used inputs and used outputs
        self.recount()

    def recount(self):
        # Update counts for used inputs and used outputs
        self.__used_inputs  = list(set(sum([x.inputs  for x in self.__ops], [])))
        self.__used_outputs = list(set(sum([x.outputs for x in self.__ops], [])))
        # Check that resources haven't been exceeded
        assert len(self.__used_inputs)  <= self.__num_inputs
        assert len(self.__used_outputs) <= self.__num_outputs
        assert len(self.__ops)          <= self.__num_slots

    def remove_op(self, op):
        assert self.contains_op(op)
        self.__ops.remove(op)
        op.node = None

    def contains_op(self, op):
        assert isinstance(op, Instruction)
        return op in self.__ops

    def space_for_op(
        self, *ops, use_reg=False, wires_in=0, wires_out=0,
    ):
        all_inputs  = set(self.__used_inputs  + sum([x.inputs  for x in ops], []))
        all_outputs = set(self.__used_outputs + sum([x.outputs for x in ops], []))
        new_ops     = set(list(ops) + list(self.__ops))
        return (
            (len(all_inputs ) < (self.__num_inputs  - wires_in )) and
            (len(all_outputs) < (self.__num_outputs - wires_out)) and
            (len(new_ops    ) < self.__num_slots                )
        )

class Mesh:

    def __init__(self, rows=4, columns=4):
        self.nodes = [[Node(x, y) for y in range(columns)] for x in range(rows)]

    def __getitem__(self, key):
        if isinstance(key, tuple):
            node = self.nodes
            for item in key: node = node[item]
            return node
        else:
            return self.nodes[key]

    @property
    def all_nodes(self):
        for row in self.nodes:
            for node in row:
                yield node

    def find_input(self, bit):
        """ Find nodes where a certain PortBit is being used as an input.

        Args:
            bit: The PortBit to locate
        """
        usage = []
        for node in self.all_nodes:
            if bit in [x.bit for x in node.inputs if isinstance(x, Input)]:
                usage.append(node)
        return usage

    def find_first_vacant(
        self, op=None, start_row=0, start_column=0, **options
    ):
        """
        Find the first vacant node in the mesh - the search has two priorities
        (1) the node with the highest remaining capacity, (2) the earliest row
        in the mesh.

        Args:
            op          : Operation to fit into the node (defaults to None)
            start_row   : Only search from row X onwards (defaults to 0)
            start_column: Only search from column Y onwards (defaults to 0)
            options     : Options to pass to 'space_for_op'

        Returns: The best matching candidate node, or None if no matches found
        """
        best_cap = 0
        viable   = None
        for row in self.nodes[start_row:]:
            for node in row[start_column:]:
                if (
                    (node.capacity > best_cap                  ) and
                    (not op or node.space_for_op(op, **options))
                ):
                    viable   = node
                    best_cap = node.capacity
            if viable: break
        return viable

    def show_utilisation(self, mode="overall"):
        print("")
        print(f"{mode.capitalize()} Usage:")
        print("      " + " ".join([f"{x:^5d}" for x in range(len(self.nodes[0]))]))
        print("------" + "-".join(["-----" for x in range(len(self.nodes[0]))]))
        for r_idx, row in enumerate(self.nodes):
            row_str = ""
            for node in row:
                u_val = 0
                if   mode == "input" : u_val = node.input_usage
                elif mode == "output": u_val = node.output_usage
                elif mode == "slot"  : u_val = node.slot_usage
                else                 : u_val = node.usage
                row_str += f"{u_val:01.03f} "
            print(f"{r_idx:3d} | {row_str}")
        print("")

def signature(bit):
    # Build the signature
    if isinstance(bit, Gate):
        parts = []
        for in_bit in bit.inputs:
            parts.append(signature(in_bit))
        sig = "(" + ",".join(parts) + ")"
        if   bit.op == Operation.INVERT: sig = "N" + sig
        elif bit.op == Operation.AND   : sig = "A" + sig
        elif bit.op == Operation.NAND  : sig = "N(A" + sig + ")"
        elif bit.op == Operation.OR    : sig = "O" + sig
        elif bit.op == Operation.NOR   : sig = "N(O" + sig + ")"
        elif bit.op == Operation.XOR   : sig = "X" + sig
        elif bit.op == Operation.XNOR  : sig = "N(X" + sig + ")"
        return sig
    elif isinstance(bit, PortBit):
        return f"I{bit.id}"
    else:
        raise Exception(f"Unsupported type {type(bit)}")

def compile(module):
    # Calculate signatures for all logic nodes
    log.info("Calculating signatures for all logic nodes")
    signatures   = {}
    histogram    = {}
    dependencies = {}
    def chase(bit, depth=0):
        bit_sig  = signature(bit)
        sub_sigs = []
        if isinstance(bit, Gate):
            for in_bit in bit.inputs:
                sub_sigs += chase(in_bit, depth=(depth + 1))
        # Work out just the immediate dependencies
        base_depth = min([x[1] for x in sub_sigs]) if sub_sigs else 0
        imm_deps   = [x for x, y in sub_sigs if y == base_depth]
        signatures[bit_sig] = (bit, imm_deps)
        # Track dependency usage
        if bit_sig not in dependencies: dependencies[bit_sig] = []
        for dep in imm_deps: dependencies[dep].append(bit_sig)
        # Accumulate term usage histogram
        if bit_sig not in histogram: histogram[bit_sig] = 0
        histogram[bit_sig] += 1
        return sub_sigs + [(bit_sig, depth)]
    for flop in (x for x in module.children.values() if isinstance(x, Flop)):
        chase(flop.input[0].driver)
    # Sort signatures by most frequently used
    sorted_sigs = sorted(signatures.keys(), key=lambda x: histogram[x], reverse=True)
    log.info(
        f"Calculated {len(signatures.keys())} signatures, most usages is "
        f"{histogram[sorted_sigs[0]]}, least usages is {histogram[sorted_sigs[-1]]}"
        f", average term usage is {mean(histogram.values())}"
    )
    # Create a mesh to track usage
    mesh = Mesh(rows=6, columns=6)
    # Assemble operation chains
    log.info("Starting to schedule operations into mesh")
    terms = {}
    for sig_idx, sig in enumerate(sorted_sigs):
        bit, sub_sigs = signatures[sig]
        # For primary inputs, insert the term then skip the rest of the processing
        if isinstance(bit, PortBit):
            terms[sig] = Input(bit, [])
            continue
        # Construct sources to the operation
        sources        = []
        all_primary_ip = True
        for sub_sig in sub_sigs:
            # Skip indirect terms
            if sub_sig in terms:
                sources.append(sub_term := terms[sub_sig])
                all_primary_ip &= isinstance(sub_term, Input)
            else:
                raise Exception(f"Can't find supporting term for '{sub_sig}'")
        # Every term starts with an output wire, then these are pruned later
        drv_flops = [
            x.port.parent for x in bit.outputs if
            isinstance(x, PortBit) and isinstance(x.port.parent, Flop)
        ]
        targets = [Wire(keep=(len(drv_flops) != 0))]
        # Construct the operation
        terms[sig]        = (op := Instruction(sig, bit, sources, targets, None))
        targets[0].driver = op
        # Find the set of nodes that hold the sources
        src_ops   = [x for x in sources if isinstance(x, Instruction)]
        src_nodes = list(set([x.node for x in src_ops]))
        # Try to identify a suitable node
        node    = None
        to_move = []
        # - If all terms are primary inputs, place where those terms are already used
        if all_primary_ip:
            node = mesh.find_first_vacant(op)
        # - If inner terms exist, place in the same node or one in the next row
        else:
            # If all sources are in one node, is there space for a new entry?
            if len(src_nodes) == 1 and src_nodes[0].space_for_op(op):
                node = src_nodes[0]
            # Otherwise, can all sub-terms be moved into one node?
            if not node and len(src_nodes) > 1:
                for src_node in src_nodes:
                    if src_node.space_for_op(op, *src_ops):
                        node    = src_node
                        to_move = [x for x in src_ops if x not in node.ops]
                        break
            # Otherwise, need to find a node in the next row down
            if not node:
                last_row = max([x.position[0] for x in src_nodes])
                node     = mesh.find_first_vacant(
                    op, start_row=(last_row + 1), wires_in=len(src_ops),
                )
            # If still no node found, place anywhere
            if not node:
                node = mesh.find_first_vacant(op, wires_in=len(src_ops))
        # Check a node was found
        if not node:
            mesh.show_utilisation()
            raise Exception(f"No node has capacity for term {sig}")
        # Move any supporting terms
        for item in to_move:
            old_node = item.node
            old_node.remove_op(item)
            node.add_op(item)
            assert item not in old_node.ops
            assert item in node.ops
        # Link terms together
        for src in src_ops:
            # Within the same node, link by register
            if src.node == node:
                reg = None
                if (regs := src.target_registers):
                    reg = regs[0]
                else:
                    reg = Register()
                    src.targets.append(reg)
                op.sources.append(reg)
            # If in different nodes, link by wire
            else:
                wires = src.target_wires
                # Output wire should not have been trimmed yet
                if not wires:
                    raise Exception(f"No output wire exists from {src.sig}")
                # Connect the source wire to the operation
                op.sources.append(wires[0])
                wires[0].targets.append(op)
        # Place the term into the node
        node.add_op(op)
        # Trim unused output wires from nodes
        for node in mesh.all_nodes:
            for chk_op in node.ops:
                # If this operation has no outputs, skip
                if not chk_op.target_wires: continue
                # If there are any unplaced dependencies, don't trim yet
                if [x for x in dependencies[chk_op.sig] if x not in terms]:
                    continue
                # Check if wire is marked with 'keep'
                if [x for x in chk_op.target_wires if x.keep]: continue
                # Check if target operations happen within one node
                tgt_nodes = set([terms[x].node for x in dependencies[chk_op.sig]])
                if len(tgt_nodes) != 1 or tgt_nodes.pop() != node: continue
                # Trim output wires
                for wire in chk_op.target_wires: chk_op.targets.remove(wire)
        # Trigger usage recounts on source nodes
        for src_node in set([x.node for x in src_ops]): src_node.recount()
    # Work out where every operation has been placed
    gate_map = {}
    for node in mesh.all_nodes:
        for op_idx, op in enumerate(node.ops):
            gate_map[op.op.id] = (node, op_idx)
    # Build up a list of messages that need to be sent
    comb_msg   = []
    seq_msg    = []
    io_out_msg = []
    for node in mesh.all_nodes:
        for op_idx, op in enumerate(node.ops):
            for output in op.op.outputs:
                if isinstance(output, Gate):
                    tgt_node, tgt_op_idx = gate_map[output.id]
                    # If within the same node, no message required
                    if tgt_node == node: continue
                    # Create a message
                    comb_msg.append(((node, op_idx), (tgt_node, tgt_op_idx)))
                elif isinstance(output, PortBit):
                    if isinstance(output.port.parent, Flop):
                        flop = output.port.parent
                        for tgt in (flop.output[0].targets if flop.output else []):
                            if isinstance(tgt, Gate):
                                tgt_node, tgt_op_idx = gate_map[tgt.id]
                                seq_msg.append(((node, op_idx), (tgt_node, tgt_op_idx)))
                            else:
                                io_out_msg.append(((node, op_idx), tgt))
                        for tgt in (flop.output_inv[0].targets if flop.output_inv else []):
                            if isinstance(tgt, Gate):
                                tgt_node, tgt_op_idx = gate_map[tgt.id]
                                seq_msg.append(((node, op_idx), (tgt_node, tgt_op_idx)))
                            else:
                                io_out_msg.append(((node, op_idx), tgt))
                    else:
                        import pdb; pdb.set_trace()
    msg_counts = {}
    for (node, op_idx), _ in (comb_msg + seq_msg + io_out_msg):
        if node.position not in msg_counts: msg_counts[node.position] = 0
        msg_counts[node.position] += 1
    ord_pos = sorted(msg_counts.keys(), key=lambda x: msg_counts[x])
    log.info(f"Total messages {len(comb_msg+seq_msg+io_out_msg)}")
    log.info(f" - Max count: {msg_counts[ord_pos[-1]]} @ {ord_pos[-1]}")
    log.info(f" - Min count: {msg_counts[ord_pos[0]]} @ {ord_pos[0]}")
    log.info(f" - Avg count: {round(mean(msg_counts.values()))}")
    # Debugging information
    mesh.show_utilisation()
    mesh.show_utilisation("input")
    mesh.show_utilisation("output")
    mesh.show_utilisation("slot")

