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

from ..models.constant import Constant
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

class State:
    def __init__(self, bit, source, targets):
        self.bit     = bit
        self.source  = source
        self.targets = targets

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
        self, row, column, inputs=8, outputs=8, slots=12, registers=8
    ):
        # Position within the mesh
        self.position = (row, column)
        # Keep a record of available resources
        self.__num_inputs    = inputs
        self.__num_outputs   = outputs
        self.__num_slots     = slots
        self.__num_registers = registers
        # Keep track of how many of each type of resource is consumed
        self.__used_inputs    = 0
        self.__used_outputs   = 0
        self.__used_registers = []
        # Keep a list of all operations
        self.__ops = []

    def __repr__(self):
        return (
            f"<Node {self.position} - "
            f"In: {self.__used_inputs}/{self.__num_inputs}, "
            f"Out: {self.__used_outputs}/{self.__num_outputs}, "
            f"Ops: {len(self.__ops)}/{self.__num_slots}>"
        )

    @property
    def input_usage(self): return (self.__used_inputs / self.__num_inputs)
    @property
    def output_usage(self): return (self.__used_outputs / self.__num_outputs)
    @property
    def slot_usage(self): return (len(self.__ops) / self.__num_slots)
    @property
    def ops(self): return self.__ops[:]

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

    def count_op_input_usage(self, *ops):
        op_inputs = []
        for op in ops:
            op_inputs += [
                x for x in op.sources if isinstance(x, State) or
                (isinstance(x, Instruction) and x.node != self)
            ]
        return len(set(op_inputs))

    def count_op_output_usage(self, *ops):
        op_outputs = 0
        for op in ops:
            for tgt in op.targets:
                if (
                    isinstance(tgt, State) or
                    (isinstance(tgt, Instruction) and tgt.node != self)
                ):
                    op_outputs += 1
                    break
        return op_outputs

    def count_op_usage(self, *ops):
        op_inputs, op_outputs = 0, 0
        for op in ops:
            op_inputs  += self.count_op_input_usage(op)
            op_outputs += self.count_op_output_usage(op)
        return op_inputs, op_outputs

    def recount(self):
        # Count how many inputs and outputs are required
        self.__used_inputs, self.__used_outputs = self.count_op_usage(*self.ops)
        # Check that resources haven't been exceeded
        assert self.__used_inputs  <= self.__num_inputs
        assert self.__used_outputs <= self.__num_outputs
        assert len(self.__ops)     <= self.__num_slots

    def remove_op(self, op):
        assert self.contains_op(op)
        self.__ops.remove(op)
        op.node = None

    def contains_op(self, op):
        assert isinstance(op, Instruction)
        return op in self.__ops

    def space_for_op(self, *ops):
        new_inputs, new_outputs = self.count_op_usage(*self.ops, *ops)
        return (
            (new_inputs                 < self.__num_inputs ) and
            (new_outputs                < self.__num_outputs) and
            ((len(ops) + len(self.ops)) < self.__num_slots  )
        )

    def encode(self, op, sources, tgt_reg, output):
        assert len(sources) <= 2
        sources += [(0, 0)] * (2 - len(sources)) if len(sources) < 2 else []
        return (
            ((int(op.op.op) & 0x7         ) << 12) | # [14:12] - OPCODE
            ((sources[0][1] & 0x7         ) <<  9) | # [11: 9] - SOURCE A
            ((1 if sources[0][0] else 0   ) <<  8) | # [ 8: 8] - INPUT/!REG A
            ((sources[1][1] & 0x7         ) <<  5) | # [ 7: 5] - SOURCE B
            ((1 if sources[1][0] else 0   ) <<  4) | # [ 4: 4] - INPUT/!REG B
            ((tgt_reg & 0x7               ) <<  1) | # [ 3: 1] - TARGET
            ((1 if (output != None) else 0) <<  0)   # [ 0: 0] - OUTPUT
        )

    def decode(self, op):
        assert isinstance(op, int)
        is_in_a = (op >>  8) & 0x1
        is_in_b = (op >>  4) & 0x1
        return {
            "OPCODE"   : Operation((op >> 12) & 0x7).name,
            "SOURCE A" : ("INPUT[" if is_in_a else "REG[") + str((op >>  9) & 0x7) + "]",
            "SOURCE B" : ("INPUT[" if is_in_a else "REG[") + str((op >>  5) & 0x7) + "]",
            "TGT REG"  : f"REG[{(op >>  1) & 0x7}]",
            "OUTPUT"   : "YES" if ((op >> 0) & 0x1) else "NO",
        }

    def compile_operations(self):
        """ Compile operations allocated to this node into encoded values

        Returns: Tuple of input allocation map, output allocation map, bytecode
                 encoded operations
        """
        regs    = [None] * self.__num_registers
        inputs  = [None] * self.__num_inputs
        outputs = [None] * self.__num_outputs
        encoded = []
        for op_idx, op in enumerate(self.ops):
            # If no free registers, raise an exception
            if None not in regs:
                raise Exception(f"Run out of registers in node {self.position}")
            # Does this operation need any external inputs?
            op_sources = []
            for src in op.sources:
                # Is this source already placed?
                if src in inputs:
                    op_sources.append((True, inputs.index(src)))
                    continue
                # If this is a registered value, use it
                if src in regs:
                    op_sources.append((False, regs.index(src)))
                    continue
                # If this is a constant, ignore it
                if isinstance(src, Constant): continue
                # If this is an internal instruction, raise an error
                if isinstance(src, Instruction) and src in self.ops:
                    raise Exception(
                        f"Failed to locate registered op in node {self.position}"
                    )
                # Otherwise, allocate the first free slot
                if None not in inputs:
                    raise Exception(f"Run out of inputs in node {self.position}")
                use_input = inputs.index(None)
                log.debug(f"N: {self.position}, O: {op_idx} -> IN[{use_input}]")
                inputs[use_input] = src
                op_sources.append((True, inputs.index(src)))
            # Use the first free register as temporary storage
            use_reg = regs.index(None)
            log.debug(f"N: {self.position}, O: {op_idx} -> REG[{use_reg}]")
            regs[use_reg] = op
            # Does this operation generate any outputs?
            use_output = None
            if self.count_op_output_usage(op):
                if None not in outputs:
                    raise Exception(f"Run out of outputs in node {self.position}")
                use_output = outputs.index(None)
                log.debug(f"N: {self.position}, O: {op_idx} -> OUT[{use_output}]")
                outputs[use_output] = op
            # Encode the instruction
            encoded.append(self.encode(op, op_sources, use_reg, use_output))
            # Check for any registers that have freed up
            required = sum([x.sources for x in self.ops[op_idx+1:]], [])
            for reg_idx, reg in enumerate(regs):
                if reg and reg not in required:
                    log.debug(f"N: {self.position} releasing REG[{reg_idx}]")
                    regs[reg_idx] = None
        # Return I/O mappings and the bytecode instruction stream
        return inputs, outputs, encoded

    def compile_messages(self, outputs):
        """ Compile messages to be emitted by this node

        Args:
            outputs: List of instructions that are mapped to outputs, position
                     determines order messages are emitted.

        Returns: Dictionary of output bit to target operation assignment.
        """
        messages = {}
        for idx_out, op in enumerate(outputs):
            # Skip unassigned outputs
            if op == None: continue
            # Create a message list for this output
            messages[idx_out] = []
            # Find the list of nodes messages need to be sent to
            for tgt in op.targets:
                if isinstance(tgt, State):
                    for flop_tgt in tgt.targets:
                        messages[idx_out].append(flop_tgt.node)
                elif isinstance(tgt, Instruction) and tgt.node != self:
                    messages[idx_out].append(tgt.node)
            # Ensure that the list is unique
            messages[idx_out] = list(set(messages[idx_out]))
        return messages

    def compile(self):
        """ Compile operations into bytecode and generate output messages.

        Returns: Tuple of encoded operations, and messages to generate
        """
        # Compile operations, also generates I/O assignments
        _, outputs, encoded = self.compile_operations()
        # Compile messages, using output assignments as a baseline
        messages = self.compile_messages(outputs)
        # Return both operations and messages
        return encoded, messages

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
        print("=" * 80)
        print(f"{mode.capitalize()} Usage:")
        print("")
        print("      " + " ".join([f"{x:^5d}" for x in range(len(self.nodes[0]))]))
        print("------" + "-".join(["-----" for x in range(len(self.nodes[0]))]))
        values = []
        for r_idx, row in enumerate(self.nodes):
            row_str = ""
            for node in row:
                u_val = 0
                if   mode == "input" : u_val = node.input_usage
                elif mode == "output": u_val = node.output_usage
                elif mode == "slot"  : u_val = node.slot_usage
                else                 : u_val = node.usage
                row_str += f"{u_val:01.03f} "
                values.append(u_val)
            print(f"{r_idx:3d} | {row_str}")
        print("")
        print(f"Max: {max(values):.02f}, Min: {min(values):.02f}, Mean: {mean(values):.02f}")
        print("=" * 80)

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
        return sub_sigs + [(bit_sig, depth)]
    for flop in (x for x in module.children.values() if isinstance(x, Flop)):
        chase(flop.input[0].driver)
    # Build all of the combinatorial operations
    terms   = {}
    bit_map = {}
    for sig, (bit, _) in signatures.items():
        if isinstance(bit, Constant):
            bit_map[bit.id] = terms[sig] = bit
        elif isinstance(bit, Gate):
            bit_map[bit.id] = terms[sig] = Instruction(sig, bit, [], [], None)
        elif isinstance(bit, PortBit) and isinstance(bit.port.parent, Flop):
            continue
        elif isinstance(bit, PortBit) and bit.port.parent == module:
            continue
        else:
            raise Exception(f"Unsupported signature type: {sig}")
    # Build all of the flops
    for flop in (x for x in module.children.values() if isinstance(x, Flop)):
        bit_map[flop.input[0].id] = (state := State(flop.input[0], None, []))
        if flop.output:
            bit_map[flop.output[0].id]     = state
            terms[f"I{flop.output[0].id}"] = state
        if flop.output_inv:
            bit_map[flop.output_inv[0].id]     = state
            terms[f"I{flop.output_inv[0].id}"] = state
    # Link sources & targets
    for sig, (bit, sub_sigs) in signatures.items():
        op = terms[sig]
        for imm_dep in sub_sigs:
            op.sources.append(terms[imm_dep])
            terms[imm_dep].targets.append(op)
        # Does this node drive any flops?
        if isinstance(bit, Gate):
            for tgt in bit.outputs:
                if isinstance(tgt, PortBit) and isinstance(tgt.port.parent, Flop):
                    assert not bit_map[tgt.id] in op.targets
                    op.targets.append(bit_map[tgt.id])
                    bit_map[tgt.id].source = bit
    # Create a mesh to track usage
    mesh = Mesh(rows=10, columns=10)
    # Place operations into the mesh, starting with the most used
    log.info("Starting to schedule operations into mesh")
    to_place = sorted(signatures.keys(), key=lambda x: dependencies[x], reverse=True)
    while to_place:
        # Pop the next term to place
        sig = to_place.pop(0)
        # Skip placing terms that are not instructions
        if sig not in terms or not isinstance(terms[sig], Instruction): continue
        # Pickup the operation
        op = terms[sig]
        # Find the set of nodes that hold the sources
        src_ops   = [x for x in op.sources if isinstance(x, Instruction)]
        src_nodes = list(set([x.node for x in src_ops]))
        # If we're not ready to place, postpone
        if None in src_nodes:
            to_place.append(sig)
            continue
        # Try to identify a suitable node
        node    = None
        to_move = []
        # - If there are no instruction dependencies, place anywhere
        if not src_ops:
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
                    op, start_row=(last_row + 1)
                )
            # If still no node found, place anywhere
            if not node: node = mesh.find_first_vacant(op)
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
        # Place the term into the node
        node.add_op(op)
        # Trigger usage recounts on source nodes
        for src_node in set([x.node for x in src_ops]): src_node.recount()
    # Work out where every operation has been placed
    gate_map = {}
    for node in mesh.all_nodes:
        for op_idx, op in enumerate(node.ops):
            gate_map[op.op.id] = (node, op_idx)
    # Debugging information
    mesh.show_utilisation()
    mesh.show_utilisation("input")
    mesh.show_utilisation("output")
    mesh.show_utilisation("slot")
    # Compile operations in every node
    compiled_ops  = {}
    compiled_msgs = {}
    for node in mesh.all_nodes:
        compiled_ops[node.position], compiled_msgs[node.position] = node.compile()
    # Accumulate message statistics
    msg_counts = [sum([len(y) for y in x.values()]) for x in compiled_msgs.values()]
    log.info(f"Total messages {sum(msg_counts)}")
    log.info(f" - Max count: {max(msg_counts)}")
    log.info(f" - Min count: {min(msg_counts)}")
    log.info(f" - Avg count: {mean(msg_counts)}")
    # Debug
    import pdb; pdb.set_trace()

