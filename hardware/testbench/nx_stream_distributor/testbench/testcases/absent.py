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

from ..testbench import testcase

@testcase()
async def absent_single_dir(dut):
    """ Test messages streamed via each interface one at a time """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Get the width of the data
    intf_size = max(dut.dist_io.data._range)-min(dut.dist_io.data._range)+1

    # Select a random interface and lower the presence flag
    absent = randint(0, 3)
    dut.present[absent] <= 0

    # Assemble the queues
    queues = [dut.exp_north, dut.exp_east, dut.exp_south, dut.exp_west]
    if   absent == 0: queues[0] = dut.exp_east
    elif absent == 1: queues[1] = dut.exp_south
    elif absent == 2: queues[2] = dut.exp_west
    elif absent == 3: queues[3] = dut.exp_north

    # Launch a message in every direction
    for dirx, exp in enumerate(queues):
        # Send a random message towards each interface
        msg = randint(0, (1 << intf_size) - 1)
        dut.dist.append((msg, dirx))

        # Queue up message on the expected output
        exp.append((msg, 0))

        # Wait for the expected queue to drain
        while exp: await RisingEdge(dut.clk)

async def absent_multi_dir(dut, backpressure):
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

    # Select a random interface and lower the presence flag
    absent = randint(0, 3)
    dut.present[absent] <= 0

    # Assemble the queues
    exps = [
        (dut.exp_north, 0), (dut.exp_east, 1),
        (dut.exp_south, 2), (dut.exp_west, 3),
    ]
    if   absent == 0: exps[0] = (dut.exp_east,  0)
    elif absent == 1: exps[1] = (dut.exp_south, 1)
    elif absent == 2: exps[2] = (dut.exp_west,  2)
    elif absent == 3: exps[3] = (dut.exp_north, 3)

    # Queue up many messages to go to different responders
    for _ in range(1000):
        # Select a random target
        exp, dirx = choice(exps)

        # Send a random message towards each interface
        msg = randint(0, (1 << intf_size) - 1)
        dut.dist.append((msg, dirx))

        # Queue up message on the expected output
        exp.append((msg, 0))

factory = TestFactory(absent_multi_dir)
factory.add_option("backpressure", [True, False])
factory.generate_tests()
