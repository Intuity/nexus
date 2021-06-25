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

from random import randint, choice

from cocotb.regression import TestFactory
from cocotb.triggers import ClockCycles, RisingEdge

from nx_constants import Direction

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
async def stream(dut):
    """ Stream many messages with randomised backpressure """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Alter the delay probability
    dut.outbound.probability = 0.1

    # Get the width of the data
    intf_size = int(dut.dut.dut.STREAM_WIDTH)

    # Drive many messages
    for _ in range(1000):
        msg = randint(0, (1 << intf_size) - 1)
        dut.expected.append((msg, 0))
        dut.inbound.append(msg)
        await ClockCycles(dut.clk, randint(1, 50))