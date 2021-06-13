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

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.map_io.common import IOMapping
from drivers.state.common import SignalState

from ..testbench import testcase

@testcase()
async def map_inputs(dut):
    """ Map inputs and check internal state tracks """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.node_row_i <= row
    dut.node_col_i <= col

    # Work out the number of inputs
    num_inputs = max(dut.inputs._range) - min(dut.inputs._range) + 1
    row_width  = max(dut.io.intf.remote_row._range) - min(dut.io.intf.remote_row._range) + 1
    col_width  = max(dut.io.intf.remote_col._range) - min(dut.io.intf.remote_col._range) + 1
    idx_width  = max(dut.io.intf.remote_idx._range) - min(dut.io.intf.remote_idx._range) + 1

    for _ in range(100):
        # Map the I/Os in a random order
        mapped = {}
        for idx in sorted(range(num_inputs), key=lambda _: random()):
            rem_row = randint(0, 15)
            rem_col = randint(0, 15)
            rem_idx = randint(0, num_inputs-1)
            is_seq  = choice((0, 1))
            dut.io.append(IOMapping(
                index=idx, is_input=1, remote_row=rem_row, remote_col=rem_col,
                remote_idx=rem_idx, seq=is_seq, slot=0, broadcast=0,
            ))
            mapped[idx] = (rem_row, rem_col, rem_idx, is_seq)

        # Wait for the queue to drain
        while dut.io._sendQ: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 10)

        # Check the mapping
        for idx, (rem_row, rem_col, rem_idx, is_seq) in mapped.items():
            map_key = int(dut.dut.dut.input_map[idx])
            got_idx = (map_key >> (                    0)) & ((1 << idx_width) - 1)
            got_col = (map_key >> (            idx_width)) & ((1 << col_width) - 1)
            got_row = (map_key >> (col_width + idx_width)) & ((1 << row_width) - 1)
            assert rem_row == got_row, f"Input {idx} - row exp: {rem_row}, got {got_row}"
            assert rem_col == got_col, f"Input {idx} - col exp: {rem_col}, got {got_col}"
            assert rem_idx == got_idx, f"Input {idx} - idx exp: {rem_idx}, got {got_idx}"
            assert dut.dut.dut.input_seq[idx] == is_seq, \
                f"Input {idx} - sequential exp: {is_seq}, got {int(dut.dut.dut.input_seq[idx])}"

@testcase()
async def input_drive(dut):
    """ Configure input mappings, then check signal state tracks correctly """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Setup a row & column
    row, col = randint(1, 14), randint(1, 14)
    dut.node_row_i <= row
    dut.node_col_i <= col

    # Work out the number of inputs
    num_inputs = max(dut.inputs._range) - min(dut.inputs._range) + 1

    # Start monitoring the trigger signal
    triggers = 0
    async def monitor_trigger():
        nonlocal triggers
        while True:
            await RisingEdge(dut.clk)
            if dut.trigger == 1: triggers += 1
    cocotb.fork(monitor_trigger())

    # Randomly map I/Os
    mapped     = {}
    curr_state = {}
    next_state = {}
    for idx in sorted(range(num_inputs), key=lambda _: random()):
        rem_row = randint(0, 15)
        rem_col = randint(0, 15)
        rem_idx = randint(0, num_inputs-1)
        is_seq  = choice((0, 1))
        dut.io.append(IOMapping(
            index=idx, is_input=1, remote_row=rem_row, remote_col=rem_col,
            remote_idx=rem_idx, seq=is_seq, slot=0, broadcast=0,
        ))
        mapped[idx]     = (rem_row, rem_col, rem_idx, is_seq)
        curr_state[idx] = 0
        next_state[idx] = 0

    # Wait for the queue to drain
    while dut.io._sendQ: await RisingEdge(dut.clk)

    # Check the initial input state is all low
    assert dut.inputs  == 0, f"Core inputs are not zero: {int(dut.inputs):08b}"
    assert dut.trigger == 0, f"Core trigger is not zero: {int(dut.trigger)}"

    # Check no triggers have gone off
    assert triggers == 0

    # Test sequential signals
    last_triggers = triggers
    for _ in range(100):
        # Setup the 'next' state
        for idx, (rem_row, rem_col, rem_idx, is_seq) in mapped.items():
            # Skip non-sequential signals
            if not is_seq: continue
            # Send in a random state
            next_state[idx] = choice((0, 1))
            dut.signal.append(SignalState(
                remote_row=rem_row, remote_col=rem_col, remote_idx=rem_idx,
                state=next_state[idx],
            ))

        # Wait for queue to drain
        while dut.signal._sendQ: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 2)

        # Check that the current state is still valid
        for idx, state in curr_state.items():
            assert dut.inputs[idx] == state, \
                f"Core input {idx} mismatches - expecting {state}, got {int(dut.inputs[idx])}"

        # Determine if there is a delta
        delta = (next_state != curr_state)

        # Provide an external trigger
        dut.ext_trigger <= 1
        await RisingEdge(dut.clk)
        dut.ext_trigger <= 0
        await ClockCycles(dut.clk, 2)

        # Propagate next -> current
        curr_state = { x: y for x, y in next_state.items() }

        # Check that the current state has updated
        for idx, state in curr_state.items():
            assert dut.inputs[idx] == state, \
                f"Core input {idx} mismatches - expecting {state}, got {int(dut.inputs[idx])}"

        # Check for exactly one trigger
        exp_triggers = last_triggers
        if delta: exp_triggers += 1
        assert triggers == exp_triggers, \
            f"Expecting {exp_triggers} triggers, observed {triggers}"
        last_triggers = triggers

    # Test combinatorial signals
    for _ in range(100):
        # Setup combinatorial signal values (immediate propagation)
        num_triggers = 0
        for idx, (rem_row, rem_col, rem_idx, is_seq) in mapped.items():
            # Skip sequential signals
            if is_seq: continue
            # Send in a random state
            new_state = choice((0, 1))
            dut.debug(
                f"State[{idx}]: R {rem_row} C {rem_col} I {rem_idx} -> {new_state}"
            )
            dut.signal.append(SignalState(
                remote_row=rem_row, remote_col=rem_col, remote_idx=rem_idx,
                state=new_state,
            ))
            # Count number of expected triggers
            if new_state != curr_state[idx]: num_triggers += 1
            # Track state
            curr_state[idx] = next_state[idx] = new_state

        # Wait for queue to drain
        while dut.signal._sendQ: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 2)

        # Check that the current state has updated
        for idx, state in curr_state.items():
            assert dut.inputs[idx] == state, \
                f"Core input {idx} mismatches - expecting {state}, got {int(dut.inputs[idx])}"

        # Check for triggers being seen
        assert triggers == (last_triggers + num_triggers), \
            f"Base {last_triggers}, expecting {num_triggers}, observed {triggers}"
        last_triggers = triggers

    # Test all signals (combinatorial and sequential)
    last_triggers = triggers
    for _ in range(100):
        # Setup the 'next' state
        num_triggers = 0
        for idx, (rem_row, rem_col, rem_idx, is_seq) in mapped.items():
            # Send in a random state
            next_state[idx] = choice((0, 1))
            if not is_seq:
                if next_state[idx] != curr_state[idx]:
                    num_triggers += 1
                curr_state[idx] = next_state[idx]
            dut.signal.append(SignalState(
                remote_row=rem_row, remote_col=rem_col, remote_idx=rem_idx,
                state=next_state[idx],
            ))

        # Wait for queue to drain
        while dut.signal._sendQ: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 2)

        # Check the current state is valid
        for idx, state in curr_state.items():
            assert dut.inputs[idx] == state, \
                f"Core input {idx} mismatches - expecting {state}, got {int(dut.inputs[idx])}"

        # Determine if there is a delta
        if next_state != curr_state: num_triggers += 1

        # Provide an external trigger
        dut.ext_trigger <= 1
        await RisingEdge(dut.clk)
        dut.ext_trigger <= 0
        await ClockCycles(dut.clk, 2)

        # Propagate next -> current
        curr_state = { x: y for x, y in next_state.items() }

        # Check that the current state has updated
        for idx, state in curr_state.items():
            assert dut.inputs[idx] == state, \
                f"Core input {idx} mismatches - expecting {state}, got {int(dut.inputs[idx])}"

        # Check for exactly one trigger
        assert triggers == (last_triggers + num_triggers), \
            f"Base {last_triggers}, expecting {num_triggers}, observed {triggers}"
        last_triggers = triggers
