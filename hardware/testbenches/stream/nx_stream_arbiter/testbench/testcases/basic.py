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

from cocotb.regression import TestFactory
from cocotb.triggers import ClockCycles, RisingEdge

from ..testbench import testcase

@testcase()
async def sanity(dut):
    """ Basic testcase """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Run for 100 clock cycles
    dut.info("Running for 100 clock cycles")
    await ClockCycles(dut.clk, 100)

    # All done!
    dut.info("Finished counting cycles")

@testcase()
async def single_dir(dut):
    """ Test messages streamed via each interface one at a time """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Set the node address to a random value
    row    = randint(1, 14)
    column = randint(1, 14)

    # Get the width of the data
    intf_size = dut.outbound_io.width("data")

    for intf in (dut.north, dut.east, dut.south, dut.west):
        # Drive a number of random messages from the selected interface
        msgs = [
            (row    << 27) |
            (column << 23) |
            randint(0, (1 << (intf_size - 8)) - 1)
            for _ in range(randint(50, 100))
        ]
        for msg in msgs: intf.append(msg)
        dut.info(f"Generated {len(msgs)} messages")

        # Queue up the expected responses
        dut.expected += [(x, 0) for x in msgs]

        # Wait for the expected queue to drain
        while dut.expected: await RisingEdge(dut.clk)

async def multi_dir(dut, backpressure):
    """ Queue up many messages onto different interfaces """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Activate/deactivate backpressure
    dut.outbound.delays = backpressure

    # Get the width of the data
    intf_size = dut.outbound_io.width("data")

    # Function to generate messages
    def gen_msg():
        return [randint(0, (1 << intf_size) - 1) for _ in range(randint(50, 100))]

    # Queue up random messages onto the different drivers
    north, east, south, west = gen_msg(), gen_msg(), gen_msg(), gen_msg()

    for msg in north: dut.north.append(msg)
    for msg in east : dut.east.append(msg)
    for msg in south: dut.south.append(msg)
    for msg in west : dut.west.append(msg)

    # Construct the expected arbitration (using round robin)
    last = 0
    while north or east or south or west:
        for idx in range(4):
            dirx = (idx + last + 1) % 4
            if   dirx == 0 and north: dut.expected.append((north.pop(0), 0))
            elif dirx == 1 and east : dut.expected.append((east.pop(0),  0))
            elif dirx == 2 and south: dut.expected.append((south.pop(0), 0))
            elif dirx == 3 and west : dut.expected.append((west.pop(0),  0))
        # Capture the last direction
        last = dirx

factory = TestFactory(multi_dir)
factory.add_option("backpressure", [True, False])
factory.generate_tests()
