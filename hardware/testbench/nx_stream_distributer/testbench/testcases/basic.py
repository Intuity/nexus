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

from random import choice, randint

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

    # Get the width of the data
    intf_size = max(dut.dist_io.data._range)-min(dut.dist_io.data._range)+1

    for dirx, exp in enumerate((
        dut.exp_north, dut.exp_east, dut.exp_south, dut.exp_west
    )):
        # Send a random message towards each interface
        msg = randint(0, (1 << intf_size) - 1)
        dut.dist.append((msg, dirx))

        # Queue up message on the expected output
        exp.append((msg, 0))

        # Wait for the expected queue to drain
        while exp: await RisingEdge(dut.clk)

async def multi_dir(dut, backpressure):
    """ Queue up many messages onto different interfaces """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Activate/deactivate backpressure
    dut.north.delays = backpressure
    dut.east.delays  = backpressure
    dut.south.delays = backpressure
    dut.west.delays  = backpressure

    # Get the width of the data
    intf_size = max(dut.dist_io.data._range)-min(dut.dist_io.data._range)+1

    # Queue up many messages to go to different responders
    exps = (
        (dut.exp_north, 0), (dut.exp_east, 1),
        (dut.exp_south, 2), (dut.exp_west, 3),
    )
    for _ in range(1000):
        # Select a random target
        exp, dirx = choice(exps)

        # Send a random message towards each interface
        msg = randint(0, (1 << intf_size) - 1)
        dut.dist.append((msg, dirx))

        # Queue up message on the expected output
        exp.append((msg, 0))

factory = TestFactory(multi_dir)
factory.add_option("backpressure", [True, False])
factory.generate_tests()
