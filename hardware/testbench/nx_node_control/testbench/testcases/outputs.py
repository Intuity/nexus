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

from drivers.map_io.common import IOMapping

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

    # Work out the number of outputs
    num_outputs = max(dut.outputs._range) - min(dut.outputs._range) + 1
    row_width   = max(dut.io.intf.remote_row._range) - min(dut.io.intf.remote_row._range) + 1
    col_width   = max(dut.io.intf.remote_col._range) - min(dut.io.intf.remote_col._range) + 1

    # Map the I/Os in a random order
    mapped = {}
    for idx in sorted(range(num_outputs), key=lambda _: random()):
        rem_row = randint(0, 15)
        rem_col = randint(0, 15)
        slot    = choice((0, 1))
        bc      = choice((0, 1))
        dut.io.append(IOMapping(
            index=idx, is_input=0, remote_row=rem_row, remote_col=rem_col,
            remote_idx=0, seq=0, slot=slot, broadcast=bc,
        ))
        mapped[idx] = (rem_row, rem_col, slot, bc)

    # Wait for the queue to drain
    while dut.io._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Check the mapping
    for idx, (rem_row, rem_col, slot, bc) in mapped.items():
        if slot:
            map_key = int(dut.dut.dut.output_map_b[idx])
        else:
            map_key = int(dut.dut.dut.output_map_a[idx])
        got_col = (map_key >> (                    0)) & ((1 << col_width) - 1)
        got_row = (map_key >> (            col_width)) & ((1 << row_width) - 1)
        got_bc  = (map_key >> (row_width + col_width)) & 1
        assert rem_row == got_row, f"Output {idx} - row exp: {rem_row}, got {got_row}"
        assert rem_col == got_col, f"Output {idx} - col exp: {rem_col}, got {got_col}"
        assert bc      == got_bc, f"Output {idx} - bc exp: {bc}, got {got_bc}"