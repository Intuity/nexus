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
from cocotb.triggers import RisingEdge

from drivers.stream.common import StreamTransaction
from nxconstants import Direction

from ..testbench import testcase

@testcase()
async def single_dir(dut):
    """ Test messages streamed to each interface one at a time """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Get the width of the data
    intf_size = dut.inbound.intf.width("data")

    for dirx, exp in enumerate((
        dut.exp_north, dut.exp_east, dut.exp_south, dut.exp_west
    )):
        # Send a random message towards each interface
        msg = randint(0, (1 << intf_size) - 1)
        dut.inbound.append(StreamTransaction(data=msg, direction=Direction(dirx)))

        # Queue up message on the expected output
        exp.append(StreamTransaction(data=msg))

        # Wait for the expected queue to drain
        while exp: await RisingEdge(dut.clk)

async def multi_dir(dut, backpressure):
    """ Queue up many messages towards different interfaces """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Activate/deactivate backpressure
    dut.north.delays = backpressure
    dut.east.delays  = backpressure
    dut.south.delays = backpressure
    dut.west.delays  = backpressure

    # Get the width of the data
    intf_size = dut.inbound.intf.width("data")

    # Queue up many messages to go to different responders
    exps = (
        (dut.exp_north, Direction.NORTH), (dut.exp_east, Direction.EAST),
        (dut.exp_south, Direction.SOUTH), (dut.exp_west, Direction.WEST),
    )
    for _ in range(1000):
        # Select a random target
        exp, dirx = choice(exps)

        # Send a random message towards each interface
        msg = randint(0, (1 << intf_size) - 1)
        dut.inbound.append(StreamTransaction(data=msg, direction=dirx))

        # Queue up message on the expected output
        exp.append(StreamTransaction(data=msg))

factory = TestFactory(multi_dir)
factory.add_option("backpressure", [True, False])
factory.generate_tests()
