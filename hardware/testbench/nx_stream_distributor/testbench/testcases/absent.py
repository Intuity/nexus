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

from cocotb.handle import Force, Release
from cocotb.regression import TestFactory
from cocotb.triggers import ClockCycles, RisingEdge

from ..testbench import testcase

async def absent_single_dir(dut, absent):
    """ Test messages streamed via each interface one at a time """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Get the width of the data
    intf_size = int(dut.dut.STREAM_WIDTH)

    # Drop presence and force ready low for the absent interface
    dut.info(f"Setting {['north', 'east', 'south', 'west'][absent]} absent")
    dut.present[absent] <= 0
    if   absent == 0: dut.north.intf.ready <= Force(0)
    elif absent == 1: dut.east.intf.ready  <= Force(0)
    elif absent == 2: dut.south.intf.ready <= Force(0)
    elif absent == 3: dut.west.intf.ready  <= Force(0)

    # Assemble the queues
    queues = [ dut.exp_north, dut.exp_east, dut.exp_south, dut.exp_west]
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

    # Wait for some time after
    await ClockCycles(dut.clk, 100)

    # Release I/O forces
    if   absent == 0: dut.north.intf.ready <= Release()
    elif absent == 1: dut.east.intf.ready  <= Release()
    elif absent == 2: dut.south.intf.ready <= Release()
    elif absent == 3: dut.west.intf.ready  <= Release()

factory = TestFactory(absent_single_dir)
factory.add_option("absent", [0, 1, 2, 3])
factory.generate_tests()

async def absent_multi_dir(dut, backpressure, absent):
    """ Queue up many messages onto different interfaces """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Activate/deactivate backpressure
    dut.north.delays = backpressure
    dut.east.delays  = backpressure
    dut.south.delays = backpressure
    dut.west.delays  = backpressure

    # Get the width of the data
    intf_size = int(dut.dut.STREAM_WIDTH)

    # Drop presence and force ready low for the absent interface
    dut.present[absent] <= 0
    if   absent == 0: dut.north.intf.ready <= Force(0)
    elif absent == 1: dut.east.intf.ready  <= Force(0)
    elif absent == 2: dut.south.intf.ready <= Force(0)
    elif absent == 3: dut.west.intf.ready  <= Force(0)

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

    # Wait for the send queue to drain
    for exp, _ in exps:
        while len(exp): await RisingEdge(dut.clk)

    # Release I/O forces
    if   absent == 0: dut.north.intf.ready <= Release()
    elif absent == 1: dut.east.intf.ready  <= Release()
    elif absent == 2: dut.south.intf.ready <= Release()
    elif absent == 3: dut.west.intf.ready  <= Release()

factory = TestFactory(absent_multi_dir)
factory.add_option("backpressure", [True, False])
factory.add_option("absent", [0, 1, 2, 3])
factory.generate_tests()
