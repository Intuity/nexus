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

from cocotb.triggers import RisingEdge

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
    num_inputs  = int(dut.dut.dut.INPUTS)
    input_width = int(ceil(log2(num_inputs)))
    col_width   = int(dut.dut.dut.ADDR_COL_WIDTH)
    row_width   = int(dut.dut.dut.ADDR_ROW_WIDTH)

    # Map the outputs in order
    mapped  = {}
    inbound = choice(dut.inbound)
    for idx in range(num_outputs):
        mapped[idx] = []
        # Setup up between 1 and 8 messages per output
        for _ in range(randint(1, 8)):
            tgt_row = randint(0, (1 << row_width  ) - 1)
            tgt_col = randint(0, (1 << col_width  ) - 1)
            tgt_idx = randint(0, (1 << input_width) - 1)
            is_seq  = choice((0, 1))
            inbound.append(build_map_output(
                row, col, idx, tgt_row, tgt_col, tgt_idx, is_seq,
            ))
            mapped[idx].append((tgt_row, tgt_col, tgt_idx, is_seq))

    # Wait for all inbound drivers to drain
    for ib in dut.inbound: await ib.idle()

    # Wait for node to go idle
    while dut.idle_o == 0: await RisingEdge(dut.clk)

    # Check the mapping
    for output, targets in mapped.items():
        # Pickup the base address and final address of each output
        output_base  = int(dut.dut.dut.control.output_base_q[output])
        output_final = int(dut.dut.dut.control.output_final_q[output])
        # Check the correct number of outputs were loaded
        output_count = ((output_final - output_base) + 1)
        assert output_count == len(targets), \
            f"Output {output} - expecting {len(targets)}, recorded {output_count}"
        # Check each output mapping
        for idx, (tgt_row, tgt_col, tgt_idx, tgt_seq) in enumerate(targets):
            ram_data = int(dut.dut.dut.store.ram.memory[512 + output_base + idx])
            ram_seq  = (ram_data >> (0                          )) & 0x1
            ram_idx  = (ram_data >> (1                          )) & ((1 << input_width) - 1)
            ram_col  = (ram_data >> (1 + input_width            )) & ((1 << col_width  ) - 1)
            ram_row  = (ram_data >> (1 + input_width + col_width)) & ((1 << row_width  ) - 1)
            assert tgt_row == ram_row, \
                f"Output {output}[{idx}] - row exp: {tgt_row}, got: {ram_row}"
            assert tgt_col == ram_col, \
                f"Output {output}[{idx}] - col exp: {tgt_col}, got: {ram_col}"
            assert tgt_idx == ram_idx, \
                f"Output {output}[{idx}] - idx exp: {tgt_idx}, got: {ram_idx}"
            assert tgt_seq == ram_seq, \
                f"Output {output}[{idx}] - seq exp: {tgt_seq}, got: {ram_seq}"
