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
    used    = []
    targets = []
    offsets = [num_instr+actv_outs]
    for index in range(actv_outs):
        targets.append([])
        num_tgts = randint(1, 5)
        # Choose a number of unique targets
        for _ in range(num_tgts):
            tgt_row, tgt_col, tgt_idx = 0, 0, 0
            while True:
                tgt_row = randint(0, MAX_ROW_COUNT-1)
                tgt_col = randint(0, MAX_COLUMN_COUNT-1)
                tgt_idx = randint(0, inputs-1)
                tgt_seq = choice((0, 1))
                if (tgt_row, tgt_col, tgt_idx) not in used:
                    used.append((tgt_row, tgt_col, tgt_idx))
                    break
            dut.info(
                f"O[{index:2d}] -> R: {tgt_row:2d}, C: {tgt_col:2d}, "
                f"I: {tgt_idx:2d}, S: {tgt_seq}"
            )
            targets[index].append((tgt_row, tgt_col, tgt_idx, tgt_seq))
        # Accumulate offsets
        offsets.append(offsets[-1]+num_tgts)

    # Populate the RAM with lookup and mapping entries
    for idx_lkp, (mappings, offset) in enumerate(zip(targets, offsets)):
        dut.ram.memory[num_instr+idx_lkp] = OutputLookup(
            active=1,
            start =offset,
            stop  =offset+len(mappings)-1,
        ).pack()
        for idx_map, (tgt_row, tgt_col, tgt_idx, tgt_seq) in enumerate(mappings):
            dut.ram.memory[offset+idx_map] = OutputMapping(
                row   =tgt_row,
                column=tgt_col,
                index =tgt_idx,
                is_seq=tgt_seq,
            ).pack()

    # Change the outputs in a random order
    state = ([0] * outputs)
    for index in sorted(range(outputs), key=lambda _: random()):
        # Push the output high
        state[index] = 1
        dut.core_outputs <= sum(((x << i) for i, x in enumerate(state)))
        # If this output is active, queue up the expected messages
        if index < actv_outs:
            for tgt_row, tgt_col, tgt_idx, tgt_seq in targets[index]:
                msg = NodeSignal()
                msg.header.row     = tgt_row
                msg.header.column  = tgt_col
                msg.header.command = NodeCommand.SIGNAL
                msg.index          = tgt_idx
                msg.state          = 1
                msg.is_seq         = tgt_seq
                dut.exp_msg.append((msg.pack(), 0))
        # Wait for the queue to drain
        while dut.exp_msg: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 10)
