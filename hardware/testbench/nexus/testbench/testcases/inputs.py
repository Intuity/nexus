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

    # Work out the number of inputs
    num_rows   = int(dut.dut.dut.ROWS)
    num_cols   = int(dut.dut.dut.COLUMNS)
    num_inputs = int(dut.dut.dut.INPUTS)
    row_width  = int(dut.dut.dut.ADDR_ROW_WIDTH)
    col_width  = int(dut.dut.dut.ADDR_COL_WIDTH)
    idx_width  = math.ceil(math.log2(num_inputs))

    # Setup random input mappings for every node
    mapped = [[{} for _ in range(num_cols)] for _ in range(num_rows)]
    for row in range(num_rows):
        for col in range(num_cols):
            # Map the I/Os in a random order
            for idx in sorted(range(num_inputs), key=lambda _: random()):
                rem_row = randint(0, 15)
                rem_col = randint(0, 15)
                rem_idx = randint(0, num_inputs-1)
                is_seq  = choice((0, 1))
                dut.inbound.append(build_map_input(
                    0, row, col, 0, idx, is_seq, rem_row, rem_col, rem_idx,
                ))
                mapped[row][col][idx] = (rem_row, rem_col, rem_idx, is_seq)

    # Wait for the inbound driver to drain
    dut.info("Waiting for mappings to drain")
    while dut.inbound._sendQ: await RisingEdge(dut.clk)
    while dut.inbound.intf.valid == 1: await RisingEdge(dut.clk)

    # Wait for the idle flag to go high
    if dut.dut.dut.mesh.idle_o == 0: await RisingEdge(dut.dut.dut.mesh.idle_o)

    # Wait for some extra time
    await ClockCycles(dut.clk, 10)

    # Check the mappings
    for row in range(num_rows):
        for col in range(num_cols):
            for idx, (rem_row, rem_col, rem_idx, is_seq) in mapped[row][col].items():
                node = dut.dut.dut.mesh.g_rows[row].g_columns[col].node
                map_key = int(node.control.input_map[idx])
                got_idx = (map_key >> (                    0)) & ((1 << idx_width) - 1)
                got_col = (map_key >> (            idx_width)) & ((1 << col_width) - 1)
                got_row = (map_key >> (col_width + idx_width)) & ((1 << row_width) - 1)
                got_seq = int(node.control.input_seq[idx])
                assert rem_row == got_row, \
                    f"{row}, {col}: Input {idx} - row exp: {rem_row}, got {got_row}"
                assert rem_col == got_col, \
                    f"{row}, {col}: Input {idx} - col exp: {rem_col}, got {got_col}"
                assert rem_idx == got_idx, \
                    f"{row}, {col}: Input {idx} - idx exp: {rem_idx}, got {got_idx}"
                assert got_seq == is_seq, \
                    f"{row}, {col}: Input {idx} - seq exp: {is_seq}, got {got_seq}"
