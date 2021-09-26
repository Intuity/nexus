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
from random import choice, randint

from cocotb.triggers import ClockCycles, RisingEdge

from nxconstants import NodeCommand, NodeMapOutput

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
    col_width   = 4
    addr_width  = int(
        dut.dut.dut.mesh.g_rows[0].g_columns[0].node.control.ctrl_outputs.STORE_ADDR_W
    )

    # Setup random output mappings for every node
    mapped = [[[] for _ in range(num_cols)] for _ in range(num_rows)]
    for row in range(num_rows):
        for col in range(num_cols):
            # Map the I/Os in order
            for idx in range(num_outputs):
                mapped[row][col].append([])
                for _ in range(randint(1, 8)):
                    rem_row            = randint(0, 15)
                    rem_col            = randint(0, 15)
                    rem_idx            = randint(0,  7)
                    is_seq             = choice((0, 1))
                    msg                = NodeMapOutput()
                    msg.header.row     = row
                    msg.header.column  = col
                    msg.header.command = NodeCommand.MAP_OUTPUT
                    msg.source_index   = idx
                    msg.target_row     = rem_row
                    msg.target_column  = rem_col
                    msg.target_index   = rem_idx
                    msg.target_is_seq  = is_seq
                    dut.mesh_inbound.append(msg.pack())
                    mapped[row][col][-1].append((
                        rem_row, rem_col, rem_idx, is_seq
                    ))

    # Wait for the inbound driver to drain
    dut.info("Waiting for mappings to drain")
    await dut.mesh_inbound.idle()

    # Wait for the idle flag to go high
    if dut.status_idle_o == 0: await RisingEdge(dut.status_idle_o)

    # Wait for some extra time
    await ClockCycles(dut.clk, 10)

    # Check the mappings
    dut.info("Checking mappings")
    def get_slice(sig, msb, lsb):
        value = 0
        for idx in range(lsb, msb+1):
            value |= int(sig[idx]) << (idx - lsb)
        return value
    for row in range(num_rows):
        for col in range(num_cols):
            node = dut.dut.dut.mesh.g_rows[row].g_columns[col].node
            for output, targets in enumerate(mapped[row][col]):
                # Check output is activated
                assert node.control.output_actv_q[output] == 1
                # Pickup the base address and final address of each output
                output_base  = get_slice(
                    node.control.output_base_q,
                    (output+1)*addr_width-1, output*addr_width
                )
                output_final = get_slice(
                    node.control.output_final_q,
                    (output+1)*addr_width-1, output*addr_width
                )
                # Check the correct number of outputs were loaded
                output_count = output_final - output_base + 1
                assert output_count == len(targets), \
                    f"R{row}C{col}O{output} - Expecting {len(targets)} targets, " \
                    f"got {output_count} targets"
                # Read the data back from the RAM
                for idx, (tgt_row, tgt_col, tgt_idx, tgt_seq) in enumerate(targets):
                    ram_data = int(node.store.ram.memory[512 + output_base + idx])
                    ram_seq  = (ram_data >> 0) & 0x1
                    ram_idx  = (ram_data >> 1) & 0x1F
                    ram_col  = (ram_data >> 1 + input_width) & 0xF
                    ram_row  = (ram_data >> 1 + input_width + col_width) & 0xF
                    assert ram_seq == tgt_seq, \
                        f"R{row}C{col}O{output} - RAM: {ram_seq}, TGT: {tgt_seq}"
                    assert ram_idx == tgt_idx, \
                        f"R{row}C{col}O{output} - RAM: {ram_idx}, TGT: {tgt_idx}"
                    assert ram_col == tgt_col, \
                        f"R{row}C{col}O{output} - RAM: {ram_col}, TGT: {tgt_col}"
                    assert ram_row == tgt_row, \
                        f"R{row}C{col}O{output} - RAM: {ram_row}, TGT: {tgt_row}"
