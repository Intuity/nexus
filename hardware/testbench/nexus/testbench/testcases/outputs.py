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
    num_inputs  = int(dut.dut.dut.INPUTS)
    input_width = int(ceil(log2(num_inputs)))
    num_outputs = int(dut.dut.dut.OUTPUTS)
    col_width   = int(dut.dut.dut.ADDR_COL_WIDTH)

    # Setup random output mappings for every node
    mapped = [[[] for _ in range(num_cols)] for _ in range(num_rows)]
    for row in range(num_rows):
        for col in range(num_cols):
            # Map the I/Os in order
            for idx in range(num_outputs):
                mapped[row][col].append([])
                for _ in range(randint(1, 8)):
                    rem_row = randint(0, 15)
                    rem_col = randint(0, 15)
                    rem_idx = randint(0,  7)
                    is_seq  = choice((0, 1))
                    dut.inbound.append(build_map_output(
                        row, col, idx, rem_row, rem_col, rem_idx, is_seq
                    ))
                    mapped[row][col][-1].append((
                        rem_row, rem_col, rem_idx, is_seq
                    ))

    # Wait for the inbound driver to drain
    dut.info("Waiting for mappings to drain")
    await dut.inbound.idle()

    # Wait for the idle flag to go high
    if dut.dut.dut.mesh.idle_o == 0: await RisingEdge(dut.dut.dut.mesh.idle_o)

    # Wait for some extra time
    await ClockCycles(dut.clk, 10)

    # Check the mappings
    dut.info("Checking mappings")
    for row in range(num_rows):
        for col in range(num_cols):
            node = dut.dut.dut.mesh.g_rows[row].g_columns[col].node
            for output, targets in enumerate(mapped[row][col]):
                # Check output is activated
                assert node.control.output_actv_q[output] == 1
                # Check for the right number of messages
                output_base  = int(node.control.output_base_q[output])
                output_final = int(node.control.output_final_q[output])
                output_count = output_final - output_base + 1
                assert output_count == len(targets), \
                    f"R{row}C{col}O{output} - Expecting {output_count} targets, " \
                    f"got {len(targets)} targets"
                # Read the data back from the RAM
                for idx, (tgt_row, tgt_col, tgt_idx, tgt_seq) in enumerate(targets):
                    ram_data = int(node.store.ram.memory[512 + output_base + idx])
                    ram_seq  = (ram_data >> 0) & 0x1
                    ram_idx  = (ram_data >> 1) & 0x7
                    ram_col  = (ram_data >> 1 + input_width) & 0xF
                    ram_row  = (ram_data >> 1 + input_width + col_width) & 0xF
                    assert ram_seq == tgt_seq, \
                        f"R{row}C{col}O{output} - {ram_seq = }, {tgt_seq = }"
                    assert ram_idx == tgt_idx, \
                        f"R{row}C{col}O{output} - {ram_idx = }, {tgt_idx = }"
                    assert ram_col == tgt_col, \
                        f"R{row}C{col}O{output} - {ram_col = }, {tgt_col = }"
                    assert ram_row == tgt_row, \
                        f"R{row}C{col}O{output} - {ram_row = }, {tgt_row = }"
