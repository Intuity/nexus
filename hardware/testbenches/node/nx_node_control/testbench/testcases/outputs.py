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

from node.outputs import gen_output_mappings
from nxconstants import (NodeCommand, NodeSignal, OutputLookup, OutputMapping,
                         MAX_ROW_COUNT, MAX_COLUMN_COUNT)

from ..testbench import testcase

@testcase()
async def output_single(dut):
    """ Update single outputs and check that the right messages are emitted """
    # Reset the DUT
    await dut.reset()

    # Pickup parameters
    inputs     = int(dut.INPUTS)
    outputs    = int(dut.OUTPUTS)
    ram_addr_w = int(dut.RAM_ADDR_W)

    # Decide on the number of active outputs
    actv_outs = randint(1, outputs)
    dut.num_output <= actv_outs

    # Decide on the number of loaded instructions
    num_instr = randint(1, (1 << ram_addr_w) // 2)
    dut.num_instr <= num_instr

    # Generate mappings for each active output
    lookups, mappings = gen_output_mappings(
        actv_outs, inputs, base_off=num_instr, min_tgts=1, max_tgts=5
    )

    # Write lookup and mappings into simulated memory
    for idx_lkp, (lookup, out_mappings) in enumerate(zip(lookups, mappings)):
        dut.ram.memory[num_instr+idx_lkp] = lookup.pack()
        for idx_out, mapping in enumerate(out_mappings):
            dut.ram.memory[lookup.start+idx_out] = mapping.pack()

    # Change the outputs in a random order
    state = ([0] * outputs)
    for index in sorted(range(outputs), key=lambda _: random()):
        # Push the output high
        state[index] = 1
        dut.core_outputs <= sum(((x << i) for i, x in enumerate(state)))
        # If this output is active, queue up the expected messages
        if index < actv_outs:
            for mapping in mappings[index]:
                msg = NodeSignal()
                msg.header.row     = mapping.row
                msg.header.column  = mapping.column
                msg.header.command = NodeCommand.SIGNAL
                msg.index          = mapping.index
                msg.state          = 1
                msg.is_seq         = mapping.is_seq
                dut.exp_msg.append((msg.pack(), 0))
        # Wait for the queue to drain
        while dut.exp_msg: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 10)

@testcase()
async def output_multi(dut):
    """ Update multiple outputs at a time and test all of the outputs are generated """
    # Reset the DUT
    await dut.reset()

    # Pickup parameters
    inputs     = int(dut.INPUTS)
    outputs    = int(dut.OUTPUTS)
    ram_addr_w = int(dut.RAM_ADDR_W)

    # Decide on the number of active outputs
    actv_outs = randint(1, outputs)
    dut.num_output <= actv_outs

    # Decide on the number of loaded instructions
    num_instr = randint(1, (1 << ram_addr_w) // 2)
    dut.num_instr <= num_instr

    # Generate mappings for each active output
    lookups, mappings = gen_output_mappings(
        actv_outs, inputs, base_off=num_instr, min_tgts=0, max_tgts=5
    )

    # Write lookup and mappings into simulated memory
    for idx_lkp, (lookup, out_mappings) in enumerate(zip(lookups, mappings)):
        dut.ram.memory[num_instr+idx_lkp] = lookup.pack()
        for idx_out, mapping in enumerate(out_mappings):
            dut.ram.memory[lookup.start+idx_out] = mapping.pack()

    # Run multiple passes
    state = ([0] * outputs)
    for _ in range(100):
        # Randomise and drive a new output state
        new_state = [choice((0, 1)) for _ in range(outputs)]
        dut.core_outputs <= sum(((x << i) for i, x in enumerate(new_state)))
        # Queue up all of the messages where there is a difference
        for index in range(actv_outs):
            # Skip outputs that haven't changed
            if state[index] == new_state[index]: continue
            # Skip inactive lookups
            if lookup.active == 0: continue
            # Run through the mappings
            for mapping in mappings[index]:
                msg = NodeSignal()
                msg.header.row     = mapping.row
                msg.header.column  = mapping.column
                msg.header.command = NodeCommand.SIGNAL
                msg.index          = mapping.index
                msg.state          = new_state[index]
                msg.is_seq         = mapping.is_seq
                dut.exp_msg.append((msg.pack(), 0))
        # Update the tracked state
        state = new_state
        # Wait for the queue to drain
        while dut.exp_msg: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 10)
