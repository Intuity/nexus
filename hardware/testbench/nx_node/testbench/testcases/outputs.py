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

from nx_message import build_map_output

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

    # Work out the number of inputs
    num_outputs = int(dut.dut.dut.OUTPUTS)
    row_width   = int(dut.dut.dut.ADDR_ROW_WIDTH)
    col_width   = int(dut.dut.dut.ADDR_COL_WIDTH)

    for _ in range(100):
        # Map the I/Os in a random order
        mapped = {}
        for idx in sorted(range(num_outputs), key=lambda _: random()):
            rem_row = randint(0, 15)
            rem_col = randint(0, 15)
            slot    = choice((0, 1))
            send_bc = choice((0, 1))
            choice(dut.inbound).append(build_map_output(
                0, row, col, 0, idx, slot, send_bc, rem_row, rem_col,
            ))
            mapped[idx] = (rem_row, rem_col, slot, send_bc)

        # Wait for all inbound drivers to drain
        for ib in dut.inbound: await ib.idle()

        # Wait for node to go idle
        while dut.idle_o == 0: await RisingEdge(dut.clk)

        # Check the mapping
        for idx, (rem_row, rem_col, slot, bc) in mapped.items():
            if slot:
                map_key = int(dut.dut.dut.control.output_map_b[idx])
            else:
                map_key = int(dut.dut.dut.control.output_map_a[idx])
            got_col = (map_key >> (                    0)) & ((1 << col_width) - 1)
            got_row = (map_key >> (            col_width)) & ((1 << row_width) - 1)
            got_bc  = (map_key >> (row_width + col_width)) & 1
            assert rem_row == got_row, \
                f"O/P {idx} S {slot} - row exp: {rem_row}, got {got_row}"
            assert rem_col == got_col, \
                f"O/P {idx} S {slot} - col exp: {rem_col}, got {got_col}"
            assert bc      == got_bc,  \
                f"O/P {idx} S {slot} - bc exp: {bc}, got {got_bc}"
