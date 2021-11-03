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

from random import choice, randint

from cocotb.triggers import RisingEdge

from drivers.state.common import SignalState

from ..testbench import testcase

@testcase()
async def inputs_non_seq(dut):
    """ Exercise updates to non-sequential inputs """
    # Reset the DUT
    await dut.reset()

    # Pickup the number of inputs
    inputs = int(dut.INPUTS)

    # Track state
    state = 0

    # Randomly drive inputs and check core input state updates
    for _ in range(1000):
        # Choose a random input index and value
        index = randint(0, inputs-1)
        value = choice((0, 1))
        # Update the input state
        new_state = state
        if value: new_state |= (1 << index)
        else    : new_state &= ((1 << inputs) - 1) - (1 << index)
        changed = (new_state != state)
        state   = new_state
        # Drive the input
        dut.input.append(SignalState(index=index, sequential=False, state=value))
        await dut.input.idle()
        await RisingEdge(dut.clk)
        # Check the state
        assert dut.core_inputs == state, \
            f"Mismatch input - 0x{state:08X} != 0x{int(dut.core_inputs):08X}"
        # Check that the trigger pulses on change...
        assert dut.core_trigger == (1 if changed else 0), \
            f"Mismatch trigger - {changed} != {int(dut.core_trigger)}"
        # ...and drops one cycle later
        await RisingEdge(dut.clk)
        assert dut.core_trigger == 0, "Trigger still high, should have fallen"

@testcase()
async def inputs_seq(dut):
    """ Exercise updates to sequential inputs """
    # Reset the DUT
    await dut.reset()

    # Pickup the number of inputs
    inputs = int(dut.INPUTS)

    # Track state
    curr_state = 0
    next_state = 0

    # Run a number of passes
    for _ in range(100):
        # Make 10 input updates on each pass
        for _ in range(10):
            # Choose a random input index and value
            index = randint(0, inputs-1)
            value = choice((0, 1))
            # Update the next input state
            if value: next_state |= (1 << index)
            else    : next_state &= ((1 << inputs) - 1) - (1 << index)
            # Drive the input
            dut.input.append(SignalState(index=index, sequential=True, state=value))
        # Wait for driver to flush
        await dut.input.idle()
        await RisingEdge(dut.clk)
        # Check inputs still match current state
        assert dut.core_inputs == curr_state, \
            f"Core inputs have changed - 0x{curr_state:08X} != 0x{int(dut.core_inputs):08X}"
        # Trigger design
        dut.trigger <= 1
        await RisingEdge(dut.clk)
        dut.trigger <= 0
        await RisingEdge(dut.clk)
        # Check inputs have updated
        assert dut.core_inputs == next_state, \
            f"Core inputs haven't updated - 0x{next_state:08X} != 0x{int(dut.core_inputs):08X}"
        # Move next -> current
        curr_state = next_state

@testcase()
async def inputs_lb(dut):
    """ Check that masked outputs are looped back to inputs sequentially """
    # Reset the DUT
    await dut.reset()

    # Pickup the number of inputs
    inputs  = int(dut.INPUTS)
    outputs = int(dut.OUTPUTS)

    # Keep track of state
    state = 0

    # Run a number of iterations
    for _ in range(100):
        # Randomise the loopback mask
        lb_mask = randint(0, (1 << inputs) - 1)
        dut.lb_mask <= lb_mask
        # Drive different output patterns
        for _ in range(10):
            # Setup outputs
            out_state = randint(0, (1 << outputs) - 1)
            dut.core_outputs <= out_state
            await RisingEdge(dut.clk)
            # Check inputs haven't changed
            assert dut.core_inputs == state, \
                f"Core inputs changed - 0x{state:08X} != 0x{int(dut.core_inputs):08X}"
            # Trigger
            dut.trigger <= 1
            await RisingEdge(dut.clk)
            dut.trigger <= 0
            await RisingEdge(dut.clk)
            # Check inputs have updated
            state = out_state & lb_mask
            assert dut.core_inputs == state, \
                f"Core inputs haven't updated - 0x{state:08X} != 0x{int(dut.core_inputs):08X}"
