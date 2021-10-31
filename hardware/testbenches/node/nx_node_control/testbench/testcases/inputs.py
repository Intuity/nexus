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

    # Check the initial input state is all low
    assert dut.inputs  == 0, f"Core inputs are not zero: {int(dut.inputs):08b}"
    assert dut.trigger == 0, f"Core trigger is not zero: {int(dut.trigger)}"

    # Check no triggers have gone off
    assert triggers == 0

    # Test every signal as sequential
    curr_state = [0 for _ in range(num_inputs)]
    next_state = [0 for _ in range(num_inputs)]
    last_triggers = triggers
    for _ in range(100):
        # Setup the 'next' state
        for idx in sorted(range(num_inputs), key=lambda _: random()):
            next_state[idx] = choice((0, 1))
            dut.signal.append(SignalState(idx, True, next_state[idx]))

        # Wait for queue to drain
        while dut.signal._sendQ: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 2)

        # Check that the current state is still valid
        for idx, state in enumerate(curr_state):
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
        curr_state = next_state[:]

        # Check that the current state has updated
        for idx, state in enumerate(curr_state):
            assert dut.inputs[idx] == state, \
                f"Core input {idx} mismatches - expecting {state}, got {int(dut.inputs[idx])}"

        # Check for exactly one trigger
        exp_triggers = last_triggers
        if delta: exp_triggers += 1
        assert triggers == exp_triggers, \
            f"Expecting {exp_triggers} triggers, observed {triggers}"
        last_triggers = triggers

    # Test every signal as combinatorial
    for _ in range(100):
        # Setup combinatorial signal values (immediate propagation)
        num_triggers = 0
        for idx in sorted(range(num_inputs), key=lambda _: random()):
            # Send in a random state
            new_state = choice((0, 1))
            dut.signal.append(SignalState(idx, False, new_state))
            # Count number of expected triggers
            if new_state != curr_state[idx]: num_triggers += 1
            # Track state
            curr_state[idx] = next_state[idx] = new_state

        # Wait for queue to drain
        while dut.signal._sendQ: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 2)

        # Check that the current state has updated
        for idx, state in enumerate(curr_state):
            assert dut.inputs[idx] == state, \
                f"Core input {idx} mismatches - expecting {state}, got {int(dut.inputs[idx])}"

        # Check for triggers being seen
        assert triggers == (last_triggers + num_triggers), \
            f"Base {last_triggers}, expecting {num_triggers}, observed {triggers}"
        last_triggers = triggers

    # Test all signals as a mix of combinatorial and sequential
    last_triggers = triggers
    for _ in range(100):
        # Select which signals are sequential
        seq_sig = [choice((True, False)) for _ in range(num_inputs)]

        # Setup the 'next' state
        num_triggers = 0
        for idx, is_seq in sorted(enumerate(seq_sig), key=lambda _: random()):
            # Send in a random state
            next_state[idx] = choice((0, 1))
            if not is_seq:
                if next_state[idx] != curr_state[idx]:
                    num_triggers += 1
                curr_state[idx] = next_state[idx]
            dut.signal.append(SignalState(idx, is_seq, next_state[idx]))

        # Wait for queue to drain
        while dut.signal._sendQ: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 2)

        # Check the current state is valid
        for idx, state in enumerate(curr_state):
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
        curr_state = next_state[:]

        # Check that the current state has updated
        for idx, state in enumerate(curr_state):
            assert dut.inputs[idx] == state, \
                f"Core input {idx} mismatches - expecting {state}, got {int(dut.inputs[idx])}"

        # Check for exactly one trigger
        assert triggers == (last_triggers + num_triggers), \
            f"Base {last_triggers}, expecting {num_triggers}, observed {triggers}"
        last_triggers = triggers
