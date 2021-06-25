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
from random import randint

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

class OutputState(IntEnum):
    """ Output state """
    LOW     = 0
    HIGH    = 1
    UNKNOWN = 2

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
        assert len(inputs) in (1, 2)
        if op == Operation.INVERT:
            return not inputs[0]
        else:
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
    def randomise(cls):
        while True:
            try:
                return Instruction(randint(0, (1 << 15) - 1))
            except Exception:
                continue

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
            f"{self.op.name}[0x{self.op:02X}](" +
            ("I" if self.is_input_a else "R") + f"[{self.source_a}]" + "," +
            ("I" if self.is_input_b else "R") + f"[{self.source_b}]" + ")" +
            f" -> R[{self.target}]" + (" -> O" if self.is_output else "")
        )

    def __str__(self): return self.__repr__()

class Node(Base):
    """ A single logic compute node in the mesh """

    def __init__(self, env, row, col, inputs=8, outputs=8, registers=8):
        """ Initialise the node.

        Args:
            env      : SimPy environment
            row      : Row position in the mesh
            col      : Column position in the mesh
            inputs   : Number of supported inputs (default: 8)
            outputs  : Number of supported outputs (default: 8)
            registers: Number of temporary value registers (default: 8)
        """
        # Initialise base class
        super().__init__(env)
        # Check and store location
        assert isinstance(row, int) and row >= 0
        assert isinstance(col, int) and col >= 0
        self.position = row, col
        # Check and store parameters
        assert isinstance(inputs,    int) and inputs    >= 1
        assert isinstance(outputs,   int) and outputs   >= 1
        assert isinstance(registers, int) and registers >= 1
        self.__inputs      = [False] * inputs
        self.__next_inputs = [False] * inputs # For the next cycle
        self.__outputs     = [OutputState.LOW] * outputs
        self.__registers   = [False] * registers
        self.__ops         = []
        # Setup phase
        self.__phase = Phase.SETUP
        # Create spaces for inbound pipes (4 -> one for each of N, E, S, W)
        self.inbound = [None] * 4
        # Create real outbound pipes
        self.outbound = [None] * 4
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
        # Naming
        self.input_names = {}
        # Flags
        self.__digesting   = False
        self.__dispatching = 0

    @property
    def row(self): return self.position[0]
    @property
    def column(self): return self.position[1]
    @property
    def ops(self): return self.__ops[:]
    @property
    def input_state(self): return self.__inputs[:]
    @property
    def next_input_state(self): return self.__next_inputs[:]
    @property
    def output_state(self): return self.__outputs[:]

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
        # Check if digesting flag is set
        if self.__digesting: return False
        # Check if dispatching is non-zero
        if self.__dispatching != 0: return False
        # Otherwise, the node is idle
        return True

    # Logging aliases
    def error(self, msg): return super().error(f"[{self.row}, {self.column}] {msg}")
    def warn (self, msg): return super().warn(f"[{self.row}, {self.column}] {msg}")
    def info (self, msg): return super().info(f"[{self.row}, {self.column}] {msg}")
    def debug(self, msg): return super().debug(f"[{self.row}, {self.column}] {msg}")

    def reset(self):
        """ Reset the state of the logic node """
        self.__inputs    = [False] * len(self.__inputs)
        self.__outputs   = [OutputState.LOW] * len(self.__outputs)
        self.__registers = [False] * len(self.__registers)
        self.__ops       = []
        self.__phase     = Phase.SETUP

    def tick(self):
        """ Trigger an internal event when an simulated clock ticks """
        # Check all pipes are empty (safety)
        for pipe in self.inbound : assert not pipe or pipe.idle
        for pipe in self.outbound: assert not pipe or pipe.idle
        assert self.internal.idle
        # Unblock instruction execution
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
            assert msg.slot == len(self.__ops), "Instruction received out of order"
            self.debug(f"Loading instruction slot {msg.slot}: {msg.instr}")
            self.__ops.append(msg.instr)
        # Configure input mapping to the node
        elif msg_type == ConfigureInput:
            assert msg.tgt_pos >= 0 and msg.tgt_pos < len(self.__inputs)
            self.debug(
                f"Mapping input {msg.tgt_pos} - R: {msg.src_row}, C: {msg.src_col}"
                f" - O[{msg.src_pos}], S: {msg.state}"
            )
            self.__input_map[msg.tgt_pos] = (
                msg.src_row, msg.src_col, msg.src_pos, msg.state
            )
        # Configure output mapping from the node
        elif msg_type == ConfigureOutput:
            assert msg.out_pos >= 0 and msg.out_pos < len(self.__outputs)
            self.debug(
                f"Mapping output {msg.out_pos} - B: {msg.msg_as_bc}, D: "
                f"{msg.bc_decay}, A: {msg.msg_a_row} {msg.msg_a_col}, B: "
                f"{msg.msg_b_row} {msg.msg_b_col}"
            )
            self.__output_map[msg.out_pos] = (
                msg.msg_as_bc, msg.bc_decay,
                msg.msg_a_row, msg.msg_a_col,
                msg.msg_b_row, msg.msg_b_col,
            )
        # Handle updated signal state
        elif msg_type == SignalState:
            handled      = False
            restart_exec = False
            for input_pos, (src_row, src_col, src_pos, state) in self.__input_map.items():
                if (
                    src_row == msg.src_row and
                    src_col == msg.src_col and
                    src_pos == msg.src_pos
                ):
                    # Mark this input has been handled
                    handled = True
                    # Log if signal value hasn't changed (suboptimal)
                    # NOTE: Because the instruction loop can be restarted at any
                    #       time, the interrupt may disrupt the sending of
                    #       messages. This can mean that a state change is lost
                    #       leading to a later message where the value appears
                    #       to be repeated. Over the course of a whole tick this
                    #       is still safe, and the correct value will propagate
                    #       but repeated values may occur.
                    did_change = (self.__next_inputs[input_pos] != msg.src_val)
                    if not did_change: self.debug("No change in signal value")
                    # Log change
                    in_name = self.input_names.get(input_pos, "N/A")
                    self.debug(
                        f"{self.position} I[{input_pos}] ({in_name}) -> "
                        f"{msg.src_val} (from {msg.source})"
                    )
                    # Always update the next tick's state
                    self.__next_inputs[input_pos] = msg.src_val
                    # If this is not a stateful input, request restart
                    if did_change and not state:
                        self.__inputs[input_pos] = msg.src_val
                        restart_exec             = True
            # If message wasn't handled, it must have been badly addressed
            if not msg.broadcast and not handled:
                raise Exception(
                    f"[{self.position}] Failed to handle SignalState: {msg}"
                )
            # If a non-stateful input was detected, restart execution
            if restart_exec: self.exec_loop.interrupt()
        # Unknown message type
        else:
            raise Exception(
                f"[{self.position}] Unknown message type {msg_type.__name__}"
            )

    def dispatch(
        self,
        msg,
        bc_dirs=[Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST],
        bc_intx=True,
    ):
        """ Dispatch a message through the correct pipe.

        Args:
            msg    : The message to send
            bc_dirs: Direction to broadcast a message in
            bc_intx: Include the internal pipe in broadcast (default: True)
        """
        def do_dispatch(msg):
            # Broadcast messages are sent on every outbound pipe
            if msg.broadcast:
                # Optionally send on the internal pipe (with no propagation)
                if bc_intx:
                    cp_msg       = msg.copy()
                    cp_msg.decay = 0          # Do not propagate
                    yield self.env.process(self.internal.push(cp_msg))
                # Send on outbound pipes
                for dirx in bc_dirs:
                    # Check pipe has been connected
                    if not self.outbound[int(dirx)]: continue
                    # Copy message, decrease decay, track propagation
                    cp_msg        = msg.copy()
                    cp_msg.decay -= 1
                    cp_msg.tracking.append((self, cp_msg))
                    # Send message
                    yield self.env.process(self.outbound[int(dirx)].push(cp_msg))
            # Non-broadcast messages are directed towards their target
            else:
                # Collect tracking information on the message to debug routing
                msg.tracking.append((self, msg))
                # Determine the pipe to send through
                pipe_dir = None
                if   msg.tgt_row < self.row   : pipe = pipe_dir = Direction.NORTH
                elif msg.tgt_row > self.row   : pipe = pipe_dir = Direction.SOUTH
                elif msg.tgt_col > self.column: pipe = pipe_dir = Direction.EAST
                elif msg.tgt_col < self.column: pipe = pipe_dir = Direction.WEST
                # Check pipe has been connected
                if not self.outbound[int(pipe_dir)]: return
                # Queue up the message onto the pipe
                if pipe_dir != None:
                    yield self.env.process(self.outbound[int(pipe_dir)].push(msg))
                else:
                    yield self.env.process(self.internal.push(msg))
            # Decrement the dispatching counter
            yield self.env.timeout(1)
            self.__dispatching -= 1
            assert self.__dispatching >= 0
        # Increment the dispatching counter
        self.__dispatching += 1
        # Trigger the simpy process
        return self.env.process(do_dispatch(msg))

    def handle_messages(self):
        """ Pickup messages from one of the inbound pipes """
        last_pipe = Direction.NORTH
        seen      = {}
        while True:
            # Wait for a message on any pipe (round robin)
            pipe = None
            while True:
                # Check the internal pipe
                if len(self.internal.out_store.items) != 0:
                    pipe = self.internal
                    break
                # Check inbound pipes
                for idx in range(len(self.inbound)):
                    wrap_idx = (int(last_pipe) + idx) % len(self.inbound)
                    test     = self.inbound[wrap_idx]
                    if not test or len(test.out_store.items) == 0: continue
                    pipe      = test
                    last_pipe = Direction(wrap_idx)
                    break
                if pipe: break
                yield self.env.timeout(1)
            # Raise the digesting flag (keeps node from appearing idle)
            self.__digesting = True
            # Grab the next message from the pipe
            msg = yield self.env.process(pipe.pop())
            # Check a message hasn't been seen twice
            if type(msg).__name__ not in seen: seen[type(msg).__name__] = []
            assert msg.id not in seen[type(msg).__name__], \
                f"{self.position} Seen message {type(msg).__name__}[{msg.id}] more than once"
            seen[type(msg).__name__].append(msg.id)
            # Is the message addressed to this node?
            if msg.target == self.position or msg.broadcast:
                self.digest(msg)
            # Does this message need to be passed on
            if msg.broadcast and msg.decay > 0:
                # Decide which directions to broadcast (to avoid recirculating)
                bc_dirs = {
                    Direction.NORTH: [Direction.SOUTH, Direction.EAST, Direction.WEST],
                    Direction.SOUTH: [Direction.NORTH, Direction.EAST, Direction.WEST],
                    Direction.EAST : [Direction.WEST],
                    Direction.WEST : [Direction.EAST],
                }[last_pipe]
                yield self.dispatch(msg, bc_dirs=bc_dirs, bc_intx=False)
            elif not msg.broadcast and msg.target != self.position:
                yield self.dispatch(msg)
            # Clear the digesting flag
            self.__digesting = False

    def execute(self):
        """ Execute the instruction loop """
        prev_inputs = [False] * len(self.__inputs)
        while True:
            try:
                # Wait for a simulated clock tick
                if self.__phase != Phase.RUN:
                    yield self.__tick_event
                    assert self.__phase in (Phase.SETUP, Phase.WAIT), \
                        f"[{self.position}] Phase is currently {self.__phase.name}"
                    # Copy input state
                    for idx, val in enumerate(self.__next_inputs):
                        self.__inputs[idx] = val
                    # Switch to the RUN phase
                    self.__phase = Phase.RUN
                # Log the difference in input
                self.debug(
                    "Current: " + "".join([("1" if x else "0") for x in self.__inputs]) +
                    ", last: "  + "".join([("1" if x else "0") for x in prev_inputs])
                )
                prev_inputs = self.__inputs[:]
                # Start executing instructions
                output_idx = 0
                for op_idx, op in enumerate(self.__ops):
                    # If this operation is empty, break out
                    if op == None: break
                    # Pickup each source value
                    val_a = self.__inputs[op.source_a] if op.is_input_a else self.__registers[op.source_a]
                    val_b = self.__inputs[op.source_b] if op.is_input_b else self.__registers[op.source_b]
                    # Perform the operation
                    self.__registers[op.target] = (result := Operation.evaluate(op.op, val_a, val_b))
                    # Debug log
                    self.debug(f"Executing op {op_idx}: {op} - A: {val_a}, B: {val_b}, R: {result}")
                    # Map result to an output state
                    out_state = OutputState.HIGH if result else OutputState.LOW
                    # Generate an output if required
                    if op.is_output and self.__outputs[output_idx] != out_state:
                        # Clear held output state
                        # NOTE: This protects against interrupt arriving between
                        #       dispatch and saving state
                        self.__outputs[output_idx] = OutputState.UNKNOWN
                        # Check output mapping exists
                        assert output_idx in self.__output_map, \
                            f"Missing output {output_idx} from {self.position}"
                        # Split out map components
                        (
                            do_bc, bc_decay, tgt_a_row, tgt_a_col, tgt_b_row,
                            tgt_b_col,
                        ) = self.__output_map[output_idx]
                        # Handle broadcast messages
                        if do_bc and bc_decay > 0:
                            yield self.dispatch(SignalState(
                                self.env, 0, 0, True, bc_decay,
                                self.row, self.column, output_idx, result,
                            ))
                        # Handle targeted messages
                        elif not do_bc:
                            yield self.dispatch(SignalState(
                                self.env, tgt_a_row, tgt_a_col, False, 0,
                                self.row, self.column, output_idx, result,
                            ))
                            if (tgt_b_row, tgt_b_col) != (tgt_a_row, tgt_a_col):
                                yield self.dispatch(SignalState(
                                    self.env, tgt_b_row, tgt_b_col, False, 0,
                                    self.row, self.column, output_idx, result,
                                ))
                        # Capture output value
                        # NOTE: This reduces duplicate values being sent
                        self.__outputs[output_idx] = out_state
                    # Always increment regardless of whether a message was sent
                    if op.is_output: output_idx += 1
                    # Wait one cycle
                    yield self.env.timeout(1)
            except simpy.Interrupt:
                # Re-activate the run phase to re-run instruction execution
                self.__phase = Phase.RUN
                # Possible to receive multiple interrupts in one cycle - let it
                # stabilise
                while True:
                    try:
                        yield self.env.timeout(1)
                        break
                    except simpy.Interrupt:
                        pass
            else:
                # Return to WAIT phase
                self.__phase = Phase.WAIT
