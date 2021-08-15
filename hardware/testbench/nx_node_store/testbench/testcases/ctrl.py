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

from random import randint

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.memory.common import MemoryTransaction

from ..testbench import testcase

@testcase()
async def ctrl_memory(dut):
    """ Test storing and reading back entries from the control store """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Get the size and maximum number of control entries
    ctrl_width = int(dut.dut.CTRL_WIDTH)
    num_ctrl   = int(dut.dut.MAX_CTRL  )

    # Randomly write entries to the control store
    state = {}
    for _ in range(randint(500, 1000)):
        wr_addr = randint(0, num_ctrl-1)
        wr_data = randint(0, (1 << ctrl_width) - 1)
        dut.ctrl.append(MemoryTransaction(addr=wr_addr, wr_data=wr_data, wr_en=1))
        state[wr_addr] = wr_data

    # Wait for the entries to be written
    while dut.ctrl._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Read back all of the entries
    reads = []
    for addr in state.keys():
        reads.append(MemoryTransaction(addr, rd_en=1))
        dut.ctrl.append(reads[-1])

    # Wait for the entries to be read
    while dut.ctrl._sendQ: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Check all read entries
    for access in reads:
        assert state[access.addr] == access.rd_data, \
            f"Control read from 0x{access.addr:08X} - expected: 0x" \
            f"{state[access.addr]:08X}, got: 0x{access.rd_data:08X}"
