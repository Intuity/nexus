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

from random import choice, randint, random

from cocotb.triggers import ClockCycles, RisingEdge

from drivers.map_io.common import IOMapping
from nx_constants import Direction
from nx_message import build_sig_state

from ..testbench import testcase

@testcase()
async def map_outputs(dut):
    """ Map outputs and check internal state tracks """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.node_row_i <= row
    dut.node_col_i <= col

    # Work out the number of outputs
    num_outputs = max(dut.outputs._range) - min(dut.outputs._range) + 1
    row_width   = max(dut.io.intf.remote_row._range) - min(dut.io.intf.remote_row._range) + 1
    col_width   = max(dut.io.intf.remote_col._range) - min(dut.io.intf.remote_col._range) + 1

    # Map the I/Os in a random order
    mapped = {}
    for idx in sorted(range(num_outputs), key=lambda _: random()):
        rem_row = randint(0, 15)
        rem_col = randint(0, 15)
        slot    = choice((0, 1))
        bc      = choice((0, 1))
        dut.io.append(IOMapping(
            index=idx, is_input=0, remote_row=rem_row, remote_col=rem_col,
            remote_idx=0, seq=0, slot=slot, broadcast=bc,
        ))
        mapped[idx] = (rem_row, rem_col, slot, bc)

    # Wait for the queue to drain
    while dut.io._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Check the mapping
    for idx, (rem_row, rem_col, slot, bc) in mapped.items():
        if slot:
            map_key = int(dut.dut.dut.output_map_b[idx])
        else:
            map_key = int(dut.dut.dut.output_map_a[idx])
        got_col = (map_key >> (                    0)) & ((1 << col_width) - 1)
        got_row = (map_key >> (            col_width)) & ((1 << row_width) - 1)
        got_bc  = (map_key >> (row_width + col_width)) & 1
        assert rem_row == got_row, f"Output {idx} - row exp: {rem_row}, got {got_row}"
        assert rem_col == got_col, f"Output {idx} - col exp: {rem_col}, got {got_col}"
        assert bc      == got_bc, f"Output {idx} - bc exp: {bc}, got {got_bc}"

@testcase()
async def output_drive(dut):
    """ Drive outputs and check that the expected messages are generated """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.node_row_i <= row
    dut.node_col_i <= col

    # Work out the number of outputs
    num_outputs = max(dut.outputs._range) - min(dut.outputs._range) + 1

    # Map the I/Os in a random order
    mapped     = {}
    last_state = {}
    curr_state = {}
    for idx in sorted(range(num_outputs), key=lambda _: random()):
        rem_row_a = randint(0, 15)
        rem_col_a = randint(0, 15)
        bc_a      = choice((0, 1))
        dut.io.append(IOMapping(
            index=idx, is_input=0, remote_row=rem_row_a, remote_col=rem_col_a,
            remote_idx=0, seq=0, slot=0, broadcast=bc_a,
        ))
        # 50% of the time, use different values for slot B
        rem_row_b, rem_col_b, bc_b = rem_row_a, rem_col_a, bc_a
        if choice((True, False)):
            rem_row_b = randint(0, 15)
            rem_col_b = randint(0, 15)
            bc_b      = choice((0, 1))
        dut.io.append(IOMapping(
            index=idx, is_input=0, remote_row=rem_row_b, remote_col=rem_col_b,
            remote_idx=0, seq=0, slot=1, broadcast=bc_b,
        ))
        last_state[idx] = curr_state[idx] = 0
        dut.info(
            f"Output[{idx}] - RA: {rem_row_a:2d}, CA: {rem_col_a:2d}, BA: {bc_a:2d}, "
            f"RB: {rem_row_b:2d}, CB: {rem_col_b:2d}, BB: {bc_b:2d}"
        )
        mapped[idx] = (rem_row_a, rem_col_a, bc_a, rem_row_b, rem_col_b, bc_b)

    # Wait for the queue to drain
    while dut.io._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Drive random I/O states
    for _ in range(100):
        # Generate a random state
        for idx in range(num_outputs): curr_state[idx] = choice((0, 1))
        # Queue up expected messages
        for idx, (row_a, col_a, bc_a, row_b, col_b, bc_b) in sorted(mapped.items(), key=lambda x: x[0]):
            # If no change in state, no message will be generated
            if curr_state[idx] == last_state[idx]: continue
            # Generate expected messages from A
            if bc_a:
                bc_decay = (row_a << 4) | col_a
                msg = build_sig_state(
                    1, 0, 0, bc_decay, curr_state[idx], row, col, idx
                )
                dut.exp_msg.append((msg, int(Direction.NORTH)))
                dut.exp_msg.append((msg, int(Direction.EAST )))
                dut.exp_msg.append((msg, int(Direction.SOUTH)))
                dut.exp_msg.append((msg, int(Direction.WEST )))
            else:
                msg = build_sig_state(
                    0, row_a, col_a, 0, curr_state[idx], row, col, idx
                )
                if   row_a < row: dut.exp_msg.append((msg, int(Direction.NORTH)))
                elif row_a > row: dut.exp_msg.append((msg, int(Direction.SOUTH)))
                elif col_a < col: dut.exp_msg.append((msg, int(Direction.WEST )))
                elif col_a > col: dut.exp_msg.append((msg, int(Direction.EAST )))
            # If A & B are the same, no second message will be generated
            if (row_a, col_a, bc_a) == (row_b, col_b, bc_b): continue
            # Generate expected messages from A
            if bc_b:
                bc_decay = (row_b << 4) | col_b
                msg = build_sig_state(
                    1, 0, 0, bc_decay, curr_state[idx], row, col, idx
                )
                dut.exp_msg.append((msg, int(Direction.NORTH)))
                dut.exp_msg.append((msg, int(Direction.EAST )))
                dut.exp_msg.append((msg, int(Direction.SOUTH)))
                dut.exp_msg.append((msg, int(Direction.WEST )))
            else:
                msg = build_sig_state(
                    0, row_b, col_b, 0, curr_state[idx], row, col, idx
                )
                if   row_b < row: dut.exp_msg.append((msg, int(Direction.NORTH)))
                elif row_b > row: dut.exp_msg.append((msg, int(Direction.SOUTH)))
                elif col_b < col: dut.exp_msg.append((msg, int(Direction.WEST )))
                elif col_b > col: dut.exp_msg.append((msg, int(Direction.EAST )))
        # Drive the new state
        dut.outputs <= sum([(y << x) for x, y in curr_state.items()])
        # Keep track of the last state
        last_state = { x: y for x, y in curr_state.items() }
        # Wait for the expected message queue to drain
        while dut.exp_msg: await RisingEdge(dut.clk)
