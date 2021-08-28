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

log = logging.getLogger("compiler.compile")

class Input:
    """ Represents a boundary input to the logic """
    def __init__(self, bit, targets):
        self.bit     = bit
        self.targets = targets

    def __repr__(self): return f"<Input {self.bit}>"

class Output:
    """ Represents a boundary output from the logic """
    def __init__(self, bit, source):
        self.bit    = bit
        self.source = source

    def __repr__(self): return f"<Output {self.bit}>"

class State:
    def __init__(self, bit, source, targets):
        self.bit     = bit
        self.source  = source
        self.targets = targets

class Instruction:

    def __init__(self, op, sources, targets, node):
        self.op      = op
        self.sources = sources
        self.targets = targets
        self.node    = node


class Node:
    """
    Represents a logic node within the mesh, keeps track of input, output, and
    instruction slot usage. Also performs compilation of operations into encoded
    values, generation of input handling and output handling.
    """

    def __init__(
        self, mesh, row, column, inputs=8, outputs=8, slots=12, registers=8
    ):
        """ Initialise the Node.

        Args:
            mesh     : Pointer to the mesh
            row      : Row position within the mesh
            column   : Column position within the mesh
            inputs   : Number of input positions
            outputs  : Number of output positions
            slots    : Maximum number of operations
            registers: Number of working registers
        """
        # Keep a reference to the mesh
        self.mesh = mesh
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
            ((int(op.op.op) & 0x7         ) << 18) | # [20:18] - OPCODE
            ((sources[0][1] & 0x1F        ) << 13) | # [17:13] - SOURCE A
            ((1 if sources[0][0] else 0   ) << 12) | # [12:12] - INPUT/!REG A
            ((sources[1][1] & 0x1F        ) <<  7) | # [11: 7] - SOURCE B
            ((1 if sources[1][0] else 0   ) <<  6) | # [ 6: 6] - INPUT/!REG B
            ((tgt_reg & 0x1F              ) <<  1) | # [ 5: 1] - TARGET
            ((1 if (output != None) else 0) <<  0)   # [ 0: 0] - OUTPUT
        )

    def decode(self, op):
        assert isinstance(op, int)
        is_in_a = (op >> 12) & 0x1
        is_in_b = (op >>  6) & 0x1
        return {
            "OPCODE"   : Operation((op >> 12) & 0x7).name,
            "SOURCE A" : ("INPUT[" if is_in_a else "REG[") + str((op >> 13) & 0x1F) + "]",
            "SOURCE B" : ("INPUT[" if is_in_b else "REG[") + str((op >>  7) & 0x1F) + "]",
            "TGT REG"  : f"REG[{(op >>  1) & 0x1F}]",
            "OUTPUT"   : "YES" if ((op >> 0) & 0x1) else "NO",
        }

    def compile_operations(self):
        """ Compile operations allocated to this node into encoded values

        Returns: Tuple of input allocation map, output allocation map, bytecode
                 encoded operations
        """
        # Sort all of the operations based on dependencies
        unordered = self.ops[:]
        ordered   = []
        while unordered:
            for op in unordered:
                satisified = True
                for src in op.sources:
                    satisified &= (
                        # It must be an instruction to affect order and...
                        (not isinstance(src, Instruction)) or
                        # ...it must be an instruction of this node...
                        (src not in self.ops             ) or
                        # ...it must be pending placement
                        (src in ordered                  )
                    )
                    # If not satisfied, move on
                    if not satisified: break
                # If satisfied, place this operation
                if satisified:
                    ordered.append(op)
                    unordered.remove(op)
                    break
        assert len(unordered) == 0, f"Failed to order {len(unordered)} ops"
        # Allocate input, output, and register usage
        regs    = [None] * self.__num_registers
        inputs  = [None] * self.__num_inputs
        outputs = [None] * self.__num_outputs
        encoded = []
        for op_idx, op in enumerate(ordered):
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
                if isinstance(src, Instruction) and src in ordered:
                    raise Exception(
                        f"{self.position} - {op_idx}/{len(ordered)}: Could not"
                        f" locate source '{src.op.id}' for '{op.op.id}'"
                    )
                # Otherwise, allocate the first free slot
                if None not in inputs:
                    raise Exception(f"Run out of inputs in node {self.position}")
                use_input = inputs.index(None)
                log.debug(
                    f"{self.position} - {op_idx}/{len(ordered)}: IN[{use_input}]"
                )
                inputs[use_input] = src
                op_sources.append((True, inputs.index(src)))
            # Use the first free register as temporary storage
            use_reg = regs.index(None)
            log.debug(
                f"{self.position} - {op_idx}/{len(ordered)}: REG[{use_reg}]"
            )
            regs[use_reg] = op
            # Does this operation generate any outputs?
            use_output = None
            if self.count_op_output_usage(op):
                if None not in outputs:
                    raise Exception(f"Run out of outputs in node {self.position}")
                use_output = outputs.index(None)
                log.debug(
                    f"{self.position} - {op_idx}/{len(ordered)}: OUT[{use_output}]"
                )
                outputs[use_output] = op
            # Encode the instruction
            encoded.append(self.encode(op, op_sources, use_reg, use_output))
            # Check for any registers that have freed up
            required = sum([x.sources for x in ordered[op_idx+1:]], [])
            for reg_idx, reg in enumerate(regs):
                if reg and reg not in required:
                    log.debug(
                        f"{self.position} - {op_idx}/{len(ordered)}: evicting "
                        f"{reg.op.id} from REG[{reg_idx}]"
                    )
                    regs[reg_idx] = None
        # Return I/O mappings and the bytecode instruction stream
        return inputs, outputs, encoded

class Mesh:
    """ Mesh of node models to suppport allocation and scheduling of operations """

    def __init__(self, rows=4, columns=4, **params):
        """ Initialise the Mesh.

        Args:
            rows   : Number of rows in the mesh
            columns: Number of columns in the mesh
            params : Other parameters
        """
        # Create the main mesh of nodes
        self.nodes = [
            [
                Node(
                    self, x, y,
                    **{k.replace("node_", "", 1): v for k, v in params.items() if k.startswith("node_")}
                ) for y in range(columns)
            ] for x in range(rows)
        ]
        # Create a special reserved output node
        self.output = Node(self, rows, 0)

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

    def show_utilisation(self, metric="summary"):
        """ Print out a utilisation table for different metrics.

        Args:
            metric: Which metric to tabulate (default: summary)
        """
        print("=" * 80)
        print(f"{metric.capitalize()} Usage:")
        print("")
        print("      " + " ".join([f"{x:^5d}" for x in range(len(self.nodes[0]))]))
        print("------" + "-".join(["-----" for x in range(len(self.nodes[0]))]))
        values = []
        for r_idx, row in enumerate(self.nodes):
            row_str = ""
            for node in row:
                u_val = 0
                if   metric == "input"  : u_val = node.input_usage
                elif metric == "output" : u_val = node.output_usage
                elif metric == "slot"   : u_val = node.slot_usage
                elif metric == "summary": u_val = node.usage
                else: raise Exception(f"Unknown metric {metric}")
                row_str += f"{u_val:01.03f} "
                values.append(u_val)
            print(f"{r_idx:3d} | {row_str}")
        print("")
        print(f"Max: {max(values):.02f}, Min: {min(values):.02f}, Mean: {mean(values):.02f}")
        print("=" * 80)

    def report_state(self, compiled_inputs):
        """ Produce a report on where state (flops) has been located.

        Args:
            compiled_inputs: Dictionary of compiled inputs for the whole mesh

        Returns: Keys are mesh position of the input, value is the flop
        """
        mapping = {}
        for node in self.all_nodes:
            inputs = compiled_inputs[node.position]
            for index, source in enumerate(inputs):
                if not source or not isinstance(source, State): continue
                mapping[
                    node.position[0], node.position[1], index
                ] = source.bit.port.parent
        return mapping

    def report_outputs(self, compiled_msgs):
        """ Produce a report on where top-level boundary outputs are generated.

        Args:
            compiled_msgs: Dictionary of compiled messages for the whole mesh

        Returns: Keys are the mesh position of the output, value is the output
        """
        mapping = {}
        for node in self.all_nodes:
            for index, messages in enumerate(compiled_msgs[node.position]):
                for target, tgt_node in messages:
                    if tgt_node != self.output: continue
                    mapping[
                        node.position[0], node.position[1], index
                    ] = target.bit
        return mapping

def compile(
    module,
    rows=4, columns=4,
    node_inputs=32, node_outputs=32, node_registers=8, node_slots=512,
):
    """
    Manage the compilation process - converting the logical model of the design
    into operations, messages, and handling configurations.

    Args:
        module        : The logic module to compile
        rows          : Number of rows in the mesh (default: 4)
        columns       : Number of columns in the mesh (default: 4)
        node_inputs   : Number of inputs per node
        node_outputs  : Number of outputs per node
        node_registers: Number of registers per node
        node_slots    : Number of instruction slots per node
    """
    # Create a mesh of the requested configuration
    mesh = Mesh(
        rows=rows, columns=columns,
        node_inputs=node_inputs, node_outputs=node_outputs,
        node_registers=node_registers, node_slots=node_slots,
    )
    # Convert gates to instructions, flops to state objects
    terms   = {}
    bit_map = {}
    for item in module.children.values():
        if isinstance(item, Gate):
            assert item.id not in bit_map
            assert str(item) not in terms
            bit_map[item.id] = terms[str(item)] = Instruction(item, [], [], None)
        elif isinstance(item, Flop):
            assert item.input[0].id not in bit_map
            bit_map[item.input[0].id] = state = State(item.input[0], None, [])
            if item.output:
                assert item.output[0].id not in bit_map
                bit_map[item.output[0].id] = state
            if item.output_inv:
                assert item.output_inv[0].id not in bit_map
                bit_map[item.output_inv[0].id] = state
        else:
            raise Exception(f"Unsupported child type: {item}")
    # Build boundary I/O
    for port in module.ports.values():
        assert port.is_input or port.is_output
        for bit in port.bits:
            bit_map[bit.id] = (Input if port.is_input else Output)(bit, [])
    # Link instruction I/O
    for op in (x for x in bit_map.values() if isinstance(x, Instruction)):
        for input in op.op.inputs:
            op.sources.append(bit_map[input.id])
        for output in op.op.outputs:
            op.targets.append(bit_map[output.id])
    # Link state I/O
    for state in (x for x in bit_map.values() if isinstance(x, State)):
        state.source = bit_map[state.bit.driver.id]
        if state.bit.port.parent.output:
            for tgt in state.bit.port.parent.output[0].targets:
                state.targets.append(bit_map[tgt.id])
        if state.bit.port.parent.output_inv:
            for tgt in state.bit.port.parent.output_inv[0].targets:
                state.targets.append(bit_map[tgt.id])
    # Link boundary I/O
    for port in module.ports.values():
        for bit in port.bits:
            if port.is_input:
                for tgt in bit.targets:
                    if tgt.id not in bit_map: continue
                    bit_map[bit.id].targets.append(bit_map[tgt.id])
            elif port.is_output:
                bit_map[bit.id].source = bit_map[bit.driver.id]
    # Place operations into the mesh, starting with the most used
    log.info("Starting to schedule operations into mesh")
    to_place    = list(terms.values())
    stall_count = 0
    while to_place:
        # Detect placement deadlock and abort
        if stall_count > len(to_place):
            perc = (1 - (len(to_place) / len(terms.values()))) * 100
            log.info("Unplaced operations:")
            for idx, op in enumerate(to_place):
                src_ops = [x for x in op.sources if isinstance(x, Instruction)]
                log.info(
                    f"[{idx:03d}] {type(op.op).__name__}_{op.op.id} requires " +
                    ", ".join([f"{type(x.op).__name__}_{x.op.id}" for x in src_ops])
                )
            raise Exception(
                f"Deadlock detected with {len(to_place)} operations left unplaced "
                f"from a total of {len(terms.values())} ({perc:.01f}% complete)"
            )
        # Pop the next term to place
        op = to_place.pop(0)
        assert isinstance(op, Instruction)
        # Find the set of nodes that hold the sources
        src_ops   = [x for x in op.sources if isinstance(x, Instruction)]
        src_nodes = list(set([x.node for x in src_ops]))
        # If we're not ready to place, postpone
        if None in src_nodes:
            to_place.append(op)
            stall_count += 1
            continue
        # Reset the stall count to zero if a placement is successful
        stall_count = 0
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
            raise Exception(f"No node has capacity for term {op.op}")
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
    # Compile operations for every node
    compiled_inputs  = {}
    compiled_outputs = {}
    compiled_instrs  = {}
    for node in mesh.all_nodes:
        (
            compiled_inputs[node.position],
            compiled_outputs[node.position],
            compiled_instrs[node.position],
        ) = node.compile_operations()
    # Compile internal messages for every node (sequential & combinatorial)
    compiled_msgs = {}
    for (tgt_row, tgt_col), inputs in compiled_inputs.items():
        for idx_input, input in enumerate(inputs):
            # Skip unpopulated inputs
            if not input: continue
            # Detect if input is flopped
            is_stateful = isinstance(input, State)
            # Resolve the instruction driving the connection
            true_source = input.source if is_stateful else input
            # Get source row and column
            src_row, src_col = true_source.node.position
            # Get the output index for the source
            src_idx = compiled_outputs[src_row, src_col].index(true_source)
            # Ensure message storage exists for the source node
            if (src_row, src_col) not in compiled_msgs:
                compiled_msgs[src_row, src_col] = [[] for _ in range(node_outputs)]
            # Append an internal message
            compiled_msgs[src_row, src_col][src_idx].append((
                tgt_row, tgt_col, idx_input, is_stateful
            ))
    # Build a report of where outputs are generated from, and insert messages
    # TODO: Temporarily using 'fake' nodes to receive outputs, in the longer
    #       term will separate 'internal' and 'external' messaging
    output_counter = 0
    output_drivers = {}
    for port in module.outputs:
        output_drivers[port.name] = []
        for bit in port.bits:
            driver           = bit_map[bit.driver.id]
            is_stateful      = isinstance(driver, State)
            src_row, src_col = driver.source.node.position
            src_idx          = compiled_outputs[src_row, src_col].index(driver.source)
            # Target an unused node input
            node_offset  = output_counter // node_inputs
            input_offset = output_counter % node_inputs
            row_offset   = node_offset // columns
            col_offset   = node_offset % columns
            tgt_row      = rows + row_offset
            # Record where this output will be sent to
            output_drivers[port.name].append((
                src_row, src_col, src_idx, tgt_row, col_offset, input_offset,
                is_stateful
            ))
            # Ensure message storage exists for the source node
            if (src_row, src_col) not in compiled_msgs:
                compiled_msgs[src_row, src_col] = [[] for _ in range(node_outputs)]
            # Setup a message for this output on the source node
            compiled_msgs[src_row, src_col][src_idx].append((
                tgt_row, col_offset, input_offset, is_stateful
            ))
            # Increment the output counter
            output_counter += 1
    # Accumulate message statistics
    msg_counts = [sum([len(y) for y in x]) for x in compiled_msgs.values()]
    log.info(f"Total messages {sum(msg_counts)}")
    log.info(f" - Max count: {max(msg_counts)}")
    log.info(f" - Min count: {min(msg_counts)}")
    log.info(f" - Avg count: {mean(msg_counts)}")
    # Return instruction sequences, input handling, output handling
    return (
        compiled_instrs, compiled_msgs, mesh.report_state(compiled_inputs),
        output_drivers
    )
