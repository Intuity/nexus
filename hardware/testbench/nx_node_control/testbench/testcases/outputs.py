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

from math import ceil, log2
from random import choice, randint, random

import cocotb
from cocotb.triggers import ClockCycles, Event, RisingEdge

from drivers.map_io.common import IOMapping
from nxconstants import Direction, NodeCommand, NodeSigState

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

    # Work out interface sizings
    num_inputs  = max(dut.inputs._range) - min(dut.inputs._range) + 1
    num_outputs = max(dut.outputs._range) - min(dut.outputs._range) + 1
    input_width = int(ceil(log2(num_inputs)))
    row_width   = max(dut.io.intf.tgt_row._range) - min(dut.io.intf.tgt_row._range) + 1
    col_width   = max(dut.io.intf.tgt_col._range) - min(dut.io.intf.tgt_col._range) + 1
    addr_width  = int(dut.dut.dut.ctrl_outputs.STORE_ADDR_W)

    # Check all outputs are inactive
    assert dut.dut.dut.output_actv_q == 0

    # Map the outputs in order
    mapped = {}
    total  = 0
    for output in range(num_outputs):
        mapped[output] = []
        for _ in range(randint(1, 8)):
            rem_row = randint(0, (1 << row_width) - 1)
            rem_col = randint(0, (1 << col_width) - 1)
            rem_idx = randint(0, num_inputs-1)
            rem_seq = choice((0, 1))
            dut.io.append(IOMapping(
                index=output, target_row=rem_row, target_col=rem_col,
                target_idx=rem_idx, target_seq=rem_seq,
            ))
            mapped[output].append((rem_row, rem_col, rem_idx, rem_seq))
            total += 1

    # Wait for the queue to drain
    while dut.io._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Check the correct number of mappings have been stored
    assert dut.dut.dut.output_next_q == total, \
        f"Expecting {total} mappings, hardware recorded {int(dut.dut.dut.output_next_q)}"

    # Check the mappings
    for output, targets in mapped.items():
        # Check the output is active
        assert dut.dut.dut.output_actv_q[output] == 1
        # Pickup the base address and count of this output
        def get_slice(sig, msb, lsb):
            value = 0
            for idx in range(lsb, msb+1):
                value |= int(sig[idx]) << (idx - lsb)
            return value
        output_base  = get_slice(
            dut.dut.dut.output_base_q,
            (output+1)*addr_width-1, output*addr_width
        )
        output_final = get_slice(
            dut.dut.dut.output_final_q,
            (output+1)*addr_width-1, output*addr_width
        )
        dut.info(f"Output B: 0x{output_base:04X}, F: 0x{output_final:04X}")
        # Check the correct number of outputs were loaded
        output_count = output_final - output_base + 1
        assert output_count == len(targets), \
            f"Output {output} - expecting {len(targets)}, recorded {output_count}"
        # Check each output mapping
        for idx, (tgt_row, tgt_col, tgt_idx, tgt_seq) in enumerate(targets):
            ram_data = dut.memory.memory[output_base + idx]
            ram_seq  = (ram_data >> (0                          )) & 0x1
            ram_idx  = (ram_data >> (1                          )) & ((1 << input_width) - 1)
            ram_col  = (ram_data >> (1 + input_width            )) & ((1 << row_width) - 1)
            ram_row  = (ram_data >> (1 + input_width + col_width)) & ((1 << col_width) - 1)
            ram_lb   = (ram_data >> (1 + input_width + col_width + row_width)) & 0x1
            assert tgt_row == ram_row, \
                f"Output {output}[{idx}] - row exp: {tgt_row}, got: {ram_row}"
            assert tgt_col == ram_col, \
                f"Output {output}[{idx}] - col exp: {tgt_col}, got: {ram_col}"
            assert tgt_idx == ram_idx, \
                f"Output {output}[{idx}] - idx exp: {tgt_idx}, got: {ram_idx}"
            assert tgt_seq == ram_seq, \
                f"Output {output}[{idx}] - seq exp: {tgt_seq}, got: {ram_seq}"
            exp_lb = (1 if (ram_row == row and ram_col == col) else 0)
            assert ram_lb == exp_lb, \
                f"Output {output}[{idx}] - lb exp: {exp_lb}, got: {ram_lb}"

@testcase()
async def output_drive(dut):
    """ Drive outputs and check that the expected messages are generated """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.node_row_i <= row
    dut.node_col_i <= col

    # Work out interface sizings
    num_inputs  = max(dut.inputs._range) - min(dut.inputs._range) + 1
    num_outputs = max(dut.outputs._range) - min(dut.outputs._range) + 1
    row_width   = max(dut.io.intf.tgt_row._range) - min(dut.io.intf.tgt_row._range) + 1
    col_width   = max(dut.io.intf.tgt_col._range) - min(dut.io.intf.tgt_col._range) + 1

    # Create a basic driver for the grant
    grant_flag = Event()
    async def do_grant():
        nonlocal grant_flag
        while True:
            await grant_flag.wait()
            grant_flag.clear()
            await RisingEdge(dut.clk)
            dut.grant <= 1
            await RisingEdge(dut.clk)
            dut.grant <= 0
    cocotb.fork(do_grant())

    # Work out the number of outputs
    num_outputs = max(dut.outputs._range) - min(dut.outputs._range) + 1

    # Map the outputs in order
    mapped = {}
    total  = 0
    for output in range(num_outputs):
        mapped[output] = []
        for _ in range(randint(1, 8)):
            rem_row = randint(0, (1 << row_width) - 1)
            rem_col = randint(0, (1 << col_width) - 1)
            rem_idx = randint(0, num_inputs-1)
            rem_seq = choice((0, 1))
            dut.io.append(IOMapping(
                index=output, target_row=rem_row, target_col=rem_col,
                target_idx=rem_idx, target_seq=rem_seq,
            ))
            mapped[output].append((rem_row, rem_col, rem_idx, rem_seq))
            total += 1

    # Track state of each output
    last_state = [0 for _ in range(num_outputs)]
    curr_state = [0 for _ in range(num_outputs)]

    # Wait for the queue to drain
    while dut.io._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Drive random I/O states
    for _ in range(30):
        # Generate a random state
        for idx in range(num_outputs): curr_state[idx] = choice((0, 1))
        # Run through every output
        for idx, targets in sorted(mapped.items(), key=lambda x: x[0]):
            # If no change in state, no message should be generated
            if curr_state[idx] == last_state[idx]: continue
            # Generate expected messages
            dut.info(f"Generating messages for output {idx}")
            for tgt_row, tgt_col, tgt_idx, tgt_seq in targets:
                msg = NodeSigState()
                msg.header.row     = tgt_row
                msg.header.column  = tgt_col
                msg.header.command = NodeCommand.SIG_STATE
                msg.index          = tgt_idx
                msg.is_seq         = tgt_seq
                msg.state          = curr_state[idx]
                dut.exp_msg.append((msg.pack(), 0))
                dut.info(
                    f"Expecting {tgt_row} {tgt_col} {tgt_idx} {tgt_seq} {curr_state[idx]}"
                )
        # Drive the new state
        dut.outputs <= sum([(y << x) for x, y in enumerate(curr_state)])
        # Keep track of the last state
        last_state = curr_state[:]
        # Loop until all expected messages are produced
        last_exp = -1
        while dut.exp_msg:
            # Wait for some time, then check no messages have been received
            num_exp = len(dut.exp_msg)
            if num_exp != last_exp:
                dut.info(f"Waiting for {num_exp} messages")
                last_exp = num_exp
            await ClockCycles(dut.clk, 10)
        # Delay between loops
        await ClockCycles(dut.clk, 50)
