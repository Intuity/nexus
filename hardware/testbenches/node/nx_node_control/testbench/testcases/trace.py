# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

from math import ceil
from random import choice, randint, random

from cocotb.triggers import ClockCycles, RisingEdge

from nxconstants import (NodeCommand, NodeSignal, NodeID, NodeTrace,
                         MAX_ROW_COUNT, MAX_COLUMN_COUNT, TRACE_SECTION_WIDTH)

from drivers.stream.common import StreamTransaction
from drivers.state.common import SignalState
from node.outputs import gen_output_mappings

from ..testbench import testcase

@testcase()
async def trace(dut):
    """ Exercise trace messages being produced at the end of each cycle """
    # Reset the DUT
    await dut.reset()

    # Pickup parameters
    inputs     = int(dut.INPUTS)
    outputs    = int(dut.OUTPUTS)
    ram_addr_w = int(dut.RAM_ADDR_W)

    # Decide on a row and column
    node_id = NodeID(
        row   =randint(0, MAX_ROW_COUNT-1   ),
        column=randint(0, MAX_COLUMN_COUNT-1),
    )
    dut.node_id <= node_id.pack()

    # Enable trace message generation
    dut.trace_en <= 1

    # Decide on the number of loaded instructions
    num_instr = randint(1, (1 << ram_addr_w) // 2)
    dut.num_instr <= num_instr

    # Decide on the number of active outputs
    actv_outs = randint(1, outputs)

    # Generate 0 active output mappings
    lookups, mappings = gen_output_mappings(
        outputs, inputs, actv_outs, base_off=num_instr, min_tgts=0, max_tgts=5
    )

    # Write lookup and mappings into simulated memory
    for idx_lkp, (lookup, out_mappings) in enumerate(zip(lookups, mappings)):
        dut.ram.memory[num_instr+idx_lkp] = lookup.pack()
        for idx_out, mapping in enumerate(out_mappings):
            dut.ram.memory[lookup.start+idx_out] = mapping.pack()

    # Change the outputs in a random order
    out_state = ([0] * outputs)
    for iter in range(1000):
        if (iter % 100) == 0: dut.info(f"Running iteration {iter}")
        # Alter an input
        dut.input.append(SignalState(index=0, sequential=True, state=((iter + 1) % 2)))
        await dut.input.idle()
        await RisingEdge(dut.clk)
        # Pulse the trigger
        dut.trigger <= 1
        await RisingEdge(dut.clk)
        dut.trigger <= 0
        # Drop the core's idle flag
        dut.core_idle <= 0
        await RisingEdge(dut.clk)
        # Randomly change output values over a period of time
        any_change = False
        for index in range(0, randint(0, outputs)):
            # Choose a new value
            new     = choice((0, 1))
            changed = (new != out_state[index])
            # Update held state
            out_state[index]  = new
            any_change       |= changed
            # Produce output messages if required
            if changed and lookups[index].active:
                for mapping in mappings[index]:
                    msg = NodeSignal()
                    msg.header.row     = mapping.row
                    msg.header.column  = mapping.column
                    msg.header.command = NodeCommand.SIGNAL
                    msg.index          = mapping.index
                    msg.state          = new
                    msg.is_seq         = mapping.is_seq
                    dut.exp_signal.append(StreamTransaction(msg.pack()))
        # Update the input to the control block
        dut.core_outputs <= sum(((x << i) for i, x in enumerate(out_state)))
        # Wait for some time
        await ClockCycles(dut.clk, randint(10, 50))
        # Raise the core's idle flag
        dut.core_idle <= 1
        await RisingEdge(dut.clk)
        # If any change occurred to the outputs, queue up trace messages
        if any_change:
            bitmap = sum(((x << i) for i, x in enumerate(out_state)))
            for select in range(int(ceil(outputs / TRACE_SECTION_WIDTH))):
                msg = NodeTrace()
                msg.header.row     = node_id.row
                msg.header.column  = node_id.column
                msg.header.command = NodeCommand.TRACE
                msg.select         = select
                msg.trace          = (
                    (bitmap >> (select * TRACE_SECTION_WIDTH)) & ((1 << TRACE_SECTION_WIDTH) - 1)
                )
                dut.exp_trace.append(StreamTransaction(msg.pack()))
        # Wait for all messages to trickle out
        while dut.exp_signal: await RisingEdge(dut.clk)
        while dut.exp_trace : await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
