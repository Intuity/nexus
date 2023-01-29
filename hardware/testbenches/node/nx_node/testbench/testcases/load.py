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

from random import choice, randint

from cocotb.triggers import ClockCycles

from nxconstants import (NodeCommand, NodeLoad, NodeID, LOAD_SEG_WIDTH,
                         MAX_ROW_COUNT, MAX_COLUMN_COUNT)

from ..testbench import testcase

@testcase()
async def load(dut):
    """ Load instructions into a node via messages """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Pickup parameters from the design
    ram_addr_w = int(dut.RAM_ADDR_W)
    ram_data_w = int(dut.RAM_DATA_W)

    # Decide on a row and column
    node_id = NodeID(
        row   =randint(0, MAX_ROW_COUNT-1   ),
        column=randint(0, MAX_COLUMN_COUNT-1),
    )
    dut.node_id <= node_id.pack()

    # Select an inbound pipe
    inbound = choice(dut.inbound)

    # Load random data into the node
    loaded = []
    chunks = ram_data_w // LOAD_SEG_WIDTH
    mask   = (1 << LOAD_SEG_WIDTH) - 1
    for _ in range(randint(10, (1 << ram_addr_w) - 1)):
        data = randint(0, (1 << ram_data_w) - 1)
        loaded.append(data)
        for chunk in range(ram_data_w // LOAD_SEG_WIDTH):
            msg = NodeLoad()
            msg.header.row     = node_id.row
            msg.header.column  = node_id.column
            msg.header.command = NodeCommand.LOAD
            msg.data           = (data >> ((chunks - chunk - 1) * LOAD_SEG_WIDTH)) & mask
            msg.last           = (chunk == (chunks - 1))
            inbound.append(msg.pack())

    # Wait for the driver to go idle
    dut.info(f"Waiting for {len(loaded)} loads to complete")
    await inbound.idle()
    await ClockCycles(dut.clk, 10)

    # Check the contents of the RAM
    for idx, exp_data in enumerate(loaded):
        rtl_data = int(dut.dut.u_dut.u_store.u_ram.memory[idx])
        assert exp_data == rtl_data, \
            f"Memory @ 0x{idx:08X}: RTL 0x{rtl_data:08X} != EXP 0x{exp_data:08X}"
