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

from random import randint

from cocotb.regression import TestFactory
from cocotb.triggers import ClockCycles

from drivers.stream.common import StreamTransaction

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

async def stream(dut, backpressure, gaps):
    """ Stream many messages with randomised backpressure """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Activate/deactivate backpressure
    dut.outbound.delays = backpressure

    # Alter the delay probability
    dut.outbound.probability = 0.1

    # Get the width of the data
    intf_size = dut.inbound.intf.width("data")

    # Drive many messages
    for _ in range(1000):
        msg = randint(0, (1 << intf_size) - 1)
        dut.expected.append(StreamTransaction(data=msg))
        dut.inbound.append(StreamTransaction(data=msg))
        if gaps: await ClockCycles(dut.clk, randint(1, 50))

factory = TestFactory(stream)
factory.add_option("backpressure", [True, False])
factory.add_option("gaps",         [True, False])
factory.generate_tests()
