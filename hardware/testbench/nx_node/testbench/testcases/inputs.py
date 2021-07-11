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

import math
from random import choice, randint, random

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from nx_message import build_map_input

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
    num_inputs = int(dut.dut.dut.INPUTS)
    row_width  = int(dut.dut.dut.ADDR_ROW_WIDTH)
    col_width  = int(dut.dut.dut.ADDR_COL_WIDTH)
    idx_width  = math.ceil(math.log2(num_inputs))

    for _ in range(100):
        # Map the I/Os in a random order
        mapped = {}
        for idx in sorted(range(num_inputs), key=lambda _: random()):
            rem_row = randint(0, 15)
            rem_col = randint(0, 15)
            rem_idx = randint(0, num_inputs-1)
            is_seq  = choice((0, 1))
            choice(dut.inbound).append(build_map_input(
                0, row, col, 0, idx, is_seq, rem_row, rem_col, rem_idx,
            ))
            mapped[idx] = (rem_row, rem_col, rem_idx, is_seq)

        # Wait for all inbound drivers to drain
        for ib in dut.inbound: await ib.idle()
        await ClockCycles(dut.clk, 10)

        # Check the mapping
        for idx, (rem_row, rem_col, rem_idx, is_seq) in mapped.items():
            map_key = int(dut.dut.dut.control.input_map[idx])
            got_idx = (map_key >> (                    0)) & ((1 << idx_width) - 1)
            got_col = (map_key >> (            idx_width)) & ((1 << col_width) - 1)
            got_row = (map_key >> (col_width + idx_width)) & ((1 << row_width) - 1)
            assert rem_row == got_row, f"Input {idx} - row exp: {rem_row}, got {got_row}"
            assert rem_col == got_col, f"Input {idx} - col exp: {rem_col}, got {got_col}"
            assert rem_idx == got_idx, f"Input {idx} - idx exp: {rem_idx}, got {got_idx}"
            assert dut.dut.dut.control.input_seq[idx] == is_seq, \
                f"Input {idx} - sequential exp: {is_seq}, got {int(dut.dut.dut.control.input_seq[idx])}"
