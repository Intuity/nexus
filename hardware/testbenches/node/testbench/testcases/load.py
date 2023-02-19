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

from random import choice, randint, random

from cocotb.triggers import ClockCycles

from nxconstants import NodeCommand, NodeHeader, NodeID, NodeLoad
from drivers.stream.common import StreamTransaction

from ..testbench import Testbench

@Testbench.testcase()
async def load_instr(tb):
    """ Write random data into the instruction memory """
    # Generate a memory image to load
    image    = []
    sequence = []
    for i_row in range(1024):
        image.append(row := [])
        for i_slot in range(4):
            row.append(randint(0, 255))
            sequence.append((i_row, i_slot))

    # Randomise the order to load the image
    sequence.sort(key=lambda _: random())

    # Append a transaction to a random stream interface
    inbound = [tb.ib_north, tb.ib_east, tb.ib_south, tb.ib_west]
    for i_row, i_slot in sequence:
        driver = choice(inbound)
        msg = NodeLoad(header =NodeHeader(target =NodeID(row=0, column=0).pack(),
                                          command=NodeCommand.LOAD).pack(),
                       address=(i_row << 1) | (i_slot >> 1),
                       slot   =(i_slot & 0x1),
                       data   =image[i_row][i_slot])
        driver.append(StreamTransaction(data=msg.pack()))

    # Wait for all drivers to go idle
    for driver in inbound:
        await driver.idle()

    # Allow for some settling time
    await ClockCycles(tb.clk, 10)

    # Check the state of the memory
    for i_row, row in enumerate(image):
        exp_data = sum((x << (i * 8) for i, x in enumerate(row)), 0)
        got_data = int(tb.dut.u_dut.u_inst_ram.memory[i_row].value)
        if exp_data != got_data:
            tb.error(f"Mismatch at row {i_row} - G: 0x{exp_data:08X} 0x{got_data:08X}")
