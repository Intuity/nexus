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

from enum import IntEnum

import simpy

from .base import Base
from .bitvector import BitVector
from .message import LoadInstruction, ConfigureInput, ConfigureOutput, SignalState
from .pipe import Pipe

class Direction(IntEnum):
    """ Communication directories for each of the 4 pipes exiting each node """
    NORTH = 0
    EAST  = 1
    SOUTH = 2
    WEST  = 3

class Operation(IntEnum):
    """ Encoding of operations that each node can perform """
    INVERT = 0
    AND    = 1
    NAND   = 2
    OR     = 3
    NOR    = 4
    XOR    = 5
    XNOR   = 6

    @classmethod
    def evaluate(self, op, *inputs):
        if op == Operation.INVERT:
            assert len(inputs) == 1
            return not inputs[0]
        else:
            assert len(inputs) == 2
            if   op == Operation.AND : return     (inputs[0] and inputs[1])
            elif op == Operation.NAND: return not (inputs[0] and inputs[1])
            elif op == Operation.OR  : return     (inputs[0] or inputs[1])
            elif op == Operation.NOR : return not (inputs[0] or inputs[1])
            elif op == Operation.XOR : return     (inputs[0] ^ inputs[1])
            elif op == Operation.XNOR: return not (inputs[0] ^ inputs[1])
            else: raise Exception(f"Unknown operation {op}")

class Phase(IntEnum):
    """ Operation phases """
    SETUP = 0
    WAIT  = 1
    RUN   = 2

class Instruction:
    """ A bit-op instruction to execute """

    def __init__(self, encoded):
        """ Initialise with an encoded instruction.

        Args:
            encoded: The encoded operation
        """
        self.raw = encoded
        (
            self.op,
            self.source_a, self.is_input_a,
            self.source_b, self.is_input_b,
            self.target,   self.is_output,
        ) = Instruction.decode(self.raw)

    @classmethod
    def decode(cls, encoded):
        bv = BitVector(encoded, 15)
        return (
            Operation(bv[14:12]), # opcode
                      bv[11: 9] , # Source A
                      bv[ 8: 8] , # Is input/is not register A
                      bv[ 7: 5] , # Source B
                      bv[ 4: 4] , # Is input/is not register B
                      bv[ 3: 1] , # Target register
                      bv[ 0: 0] , # Generates output
        )

    def __repr__(self):
        return (
            f"{self.op.name}(" +
            ("I" if self.is_input_a else "R") + f"[{self.source_a}]" + "," +
            ("I" if self.is_input_b else "R") + f"[{self.source_b}]" + ")" +
            f" -> R[{self.target}]" + (" -> O" if self.is_output else "")
        )

    def __str__(self): return self.__repr__()

class Node(Base):
    """ A single logic compute node in the mesh """

    def __init__(self, env, row, col, inputs=8, outputs=8, registers=8, max_ops=16):
        """ Initialise the node.

        Args:
            env      : SimPy environment
            row      : Row position in the mesh
            col      : Column position in the mesh
            inputs   : Number of supported inputs (default: 8)
            outputs  : Number of supported outputs (default: 8)
            registers: Number of temporary value registers (default: 8)
            max_ops  : Maximum number of instructions (default: 16)
        """
        # Initialise base class
        super().__init__(env)
        # Check and store location
        assert isinstance(row, int) and row >= 0
        assert isinstance(col, int) and col >= 0
        self.position = row, col
        self.debug(f"Creating node {self.position}")
        # Check and store parameters
        assert isinstance(inputs,    int) and inputs    >= 1
        assert isinstance(outputs,   int) and outputs   >= 1
        assert isinstance(registers, int) and registers >= 1
        assert isinstance(max_ops,   int) and max_ops   >= 1
        self.__inputs    = [0] * inputs
        self.__outputs   = [0] * outputs
        self.__registers = [0] * registers
        self.__ops       = [None] * max_ops
        # Setup phase
        self.__phase = Phase.SETUP
        # Create spaces for inbound pipes (4 -> one for each of N, E, S, W)
        self.inbound = [None] * 4
        # Create real outbound pipes
        self.outbound = [Pipe(self.env, 1, 1) for _ in range(4)]
        # The internal pipe allows for loopback from outputs -> inputs
        self.internal = Pipe(self.env, 1, 1)
        # Create an internal tick event
        self.__tick_event = self.env.event()
        # Setup run loop
        self.msg_loop  = self.env.process(self.handle_messages())
        self.exec_loop = self.env.process(self.execute())
        # Input mappings
        self.__input_map  = {}
        self.__output_map = {}

    @property
    def row(self): return self.position[0]
    @property
    def column(self): return self.position[1]

    @property
    def idle(self):
        # If not in setup or wait phases, the node is busy
        if self.__phase not in (Phase.SETUP, Phase.WAIT): return False
        # Check all of the inbound pipes for messages
        for pipe in self.inbound:
            if pipe and not pipe.idle: return False
        # Check all of the outbound pipes for messages
        for pipe in self.outbound:
            if pipe and not pipe.idle: return False
        # Check the internal pipe
        if not self.internal.idle: return False
        # Otherwise, the node is idle
        return True

    def reset(self):
        """ Reset the state of the logic node """
        self.__inputs    = [0] * len(self.__inputs)
        self.__outputs   = [0] * len(self.__outputs)
        self.__registers = [0] * len(self.__registers)
        self.__ops       = [None] * len(self.__ops)
        self.__phase     = Phase.SETUP

    def tick(self):
        """ Trigger an internal event when an simulated clock ticks """
        self.__tick_event.succeed()
        self.__tick_event = self.env.event()

    def digest(self, msg):
        """ Handle a received message

        Args:
            msg: The message object to digest
        """
        # Check this message is for this node?
        assert msg.broadcast or (msg.tgt_row == self.row and msg.tgt_col == self.column)
        # Extract the message type
        msg_type = type(msg)
        # Load an instruction into a specified slot
        if msg_type == LoadInstruction:
            assert msg.slot >= 0 and msg.slot < len(self.__ops)
            self.__ops[msg.slot] = msg.instr
        # Configure input mapping to the node
        elif msg_type == ConfigureInput:
            assert msg.tgt_pos >= 0 and msg.tgt_pos < len(self.__inputs)
            self.__input_map[msg.tgt_pos] = (
                msg.src_row, msg.src_col, msg.src_pos, msg.state
            )
        # Configure output mapping from the node
        elif msg_type == ConfigureOutput:
            assert msg.out_pos >= 0 and msg.out_pos < len(self.__outputs)
            self.__output_map[msg.out_pos] = (
                self.msg_as_bc, self.bc_decay,
                self.msg_a_row, self.msg_a_col,
                self.msg_b_row, self.msg_b_col,
            )
        # Handle updated signal state
        elif msg_type == SignalState:
            for input_pos, (src_row, src_col, src_pos, state) in self.__input_map.items():
                if (
                    src_row == msg.src_row and
                    src_col == msg.src_col and
                    src_pos == msg.src_pos
                ):
                    self.__inputs[input_pos] = msg.src_val
                    # If this is not a stateful input, restart instruction execution
                    if not state: self.execute.interrupt()
                    break
            else:
                raise Exception(f"Failed to handle SignalState: {msg}")
        # Unknown message type
        else:
            raise Exception(f"Unknown message type {msg_type.__name__}")

    def dispatch(
        self,
        msg,
        bc_dirs=[Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST],
    ):
        """ Dispatch a message through the correct pipe.

        Args:
            msg    : The message to send
            bc_dirs: Direction to broadcast a message in
        """
        def do_dispatch(msg):
            if msg.broadcast:
                # Queue up the message onto every pipe
                self.debug(f"[{self.position}] Broadcasting message")
                for dirx in bc_dirs:
                    yield self.env.process(self.outbound[int(dirx)].push(msg))
            else:
                # Determine the pipe to send through
                pipe_dir = None
                if   msg.tgt_row < self.row   : pipe = pipe_dir = Direction.NORTH
                elif msg.tgt_row > self.row   : pipe = pipe_dir = Direction.SOUTH
                elif msg.tgt_col > self.column: pipe = pipe_dir = Direction.EAST
                elif msg.tgt_col < self.column: pipe = pipe_dir = Direction.WEST
                # Queue up the message onto the pipe
                if pipe_dir != None:
                    self.debug(f"[{self.position}] Dispatch on {pipe_dir.name} pipe")
                    yield self.env.process(self.outbound[int(pipe_dir)].push(msg))
                else:
                    self.debug(f"[{self.position}] Dispatch on internal pipe")
                    yield self.env.process(self.internal.push(msg))
        return self.env.process(do_dispatch(msg))

    def handle_messages(self):
        """ Pickup messages from one of the inbound pipes """
        last_pipe = Direction.NORTH
        while True:
            # Wait for a message on any inbound pipe (round robin)
            self.debug(f"Node {self.position} - waiting for message")
            while True:
                pipe = None
                for idx in range(len(self.inbound)):
                    test = self.inbound[(int(last_pipe) + idx) % len(self.inbound)]
                    if not test or len(test.out_store.items) == 0: continue
                    pipe      = test
                    last_pipe = Direction(idx)
                if pipe: break
                yield self.env.timeout(1)
            self.debug(f"Node {self.position} - got message")
            # Grab the next message from the pipe
            self.debug(f"[{self.position}] Received message from pipe {last_pipe.name}")
            msg = pipe.pop()
            # Is the message addressed to this node?
            if msg.target == self.position or msg.broadcast:
                self.digest(msg)
            # Does this message need to be passed on
            if msg.target != self.position:
                yield self.dispatch(msg)
            elif msg.broadcast and msg.decay > 0:
                # Copy the message and adjust the decay
                cp_msg        = msg.copy()
                cp_msg.decay -= 1
                # Decide which directions to broadcast (to avoid recirculating)
                bc_dirs = {
                    Direction.NORTH: [Direction.SOUTH, Direction.EAST, Direction.WEST],
                    Direction.SOUTH: [Direction.NORTH, Direction.EAST, Direction.WEST],
                    Direction.EAST : [Direction.WEST],
                    Direction.WEST : [Direction.EAST],
                }[last_pipe]
                yield self.dispatch(msg, bc_dirs=bc_dirs)

    def execute(self):
        """ Execute the instruction loop """
        skip_tick = False
        while True:
            try:
                # Wait for a simulated clock tick
                if not skip_tick:
                    self.debug(f"Node {self.position} - waiting for tick")
                    yield self.__tick_event
                    assert self.__phase in (Phase.SETUP, Phase.WAIT), \
                        f"[{self.position}] Phase is currently {self.__phase.name}"
                    self.debug(f"Node {self.position} - got tick")
                # Reset skip tick (after interrupt has set it)
                skip_tick = False
                # Switch to the RUN phase
                self.__phase = Phase.RUN
                # Start executing instructions
                output_idx = 0
                for op in self.__ops:
                    # If this operation is empty, break out
                    if op == None: break
                    # Pickup each source value
                    val_a = self.__inputs[op.source_a] if op.is_input_a else self.__registers[op.source_a]
                    val_b = self.__inputs[op.source_b] if op.is_input_b else self.__registers[op.source_b]
                    # Perform the operation
                    self.__registers[op.target] = (result := Operation.evaluate(op.op, val_a, val_b))
                    # Generate an output if required
                    if op.is_output:
                        assert output_idx in self.__output_map
                        (
                            do_bc, bc_decay, tgt_a_row, tgt_a_col, tgt_b_row,
                            tgt_b_col,
                        ) = self.__output_map[output_idx]
                        if do_bc and bc_decay > 0:
                            yield dispatch(SignalState(
                                self.env, 0, 0, True, bc_decay,
                                self.row, self.column, output_idx, result,
                            ))
                        elif not do_bc:
                            yield dispatch(SignalState(
                                self.env, tgt_a_row, tgt_a_col, False, 0,
                                self.row, self.column, output_idx, result,
                            ))
                            if (tgt_b_row, tgt_b_col) != (tgt_a_row, tgt_a_col):
                                yield dispatch(SignalState(
                                    self.env, tgt_b_row, tgt_b_col, False, 0,
                                    self.row, self.column, output_dix, result,
                                ))
                    # Wait one cycle
                    yield self.env.timeout(1)
                # Return to WAIT phase
                self.__phase = Phase.WAIT
            except simpy.Interrupt:
                self.debug("Execution interrupted - restarting")
                skip_tick = True
