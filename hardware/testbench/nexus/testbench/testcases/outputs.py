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

from nx_message import build_map_output

from ..testbench import testcase

@testcase()
async def map_outputs(dut):
    """ Map outputs and check internal state tracks """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Work out the number of inputs
    num_rows    = int(dut.dut.dut.ROWS)
    num_cols    = int(dut.dut.dut.COLUMNS)
    num_outputs = int(dut.dut.dut.OUTPUTS)
    row_width   = int(dut.dut.dut.ADDR_ROW_WIDTH)
    col_width   = int(dut.dut.dut.ADDR_COL_WIDTH)

    # Setup random output mappings for every node
    mapped = [[{} for _ in range(num_cols)] for _ in range(num_rows)]
    for row in range(num_rows):
        for col in range(num_cols):
            # Map the I/Os in a random order
            for idx in sorted(range(num_outputs), key=lambda _: random()):
                rem_row = randint(0, 15)
                rem_col = randint(0, 15)
                slot    = choice((0, 1))
                send_bc = choice((0, 1))
                dut.inbound.append(build_map_output(
                    0, row, col, 0, idx, slot, send_bc, rem_row, rem_col,
                ))
                mapped[row][col][idx] = (rem_row, rem_col, slot, send_bc)

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
            for idx, (rem_row, rem_col, slot, bc) in mapped[row][col].items():
                node = dut.dut.dut.mesh.g_rows[row].g_columns[col].node
                if slot: map_key = int(node.control.output_map_b[idx])
                else   : map_key = int(node.control.output_map_a[idx])
                got_col = (map_key >> (                    0)) & ((1 << col_width) - 1)
                got_row = (map_key >> (            col_width)) & ((1 << row_width) - 1)
                got_bc  = (map_key >> (row_width + col_width)) & 1
                assert rem_row == got_row, \
                    f"{row}, {col}: O/P {idx} S {slot} - row exp: {rem_row}, got {got_row}"
                assert rem_col == got_col, \
                    f"{row}, {col}: O/P {idx} S {slot} - col exp: {rem_col}, got {got_col}"
                assert bc      == got_bc,  \
                    f"{row}, {col}: O/P {idx} S {slot} - bc exp: {bc}, got {got_bc}"
