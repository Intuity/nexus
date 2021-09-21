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

from nxconstants import Direction

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
    intf_size = max(dut.comb.intf.data._range)-min(dut.comb.intf.data._range)+1

    # Drive a number of random messages from each interface
    for intf in (dut.stream_a, dut.stream_b):
        msgs = [randint(0, (1 << intf_size) - 1) for _ in range(randint(50, 100))]
        for msg in msgs: intf.append((msg, 0))
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
    dut.comb.delays = backpressure

    # Get the width of the data
    intf_size = max(dut.comb.intf.data._range)-min(dut.comb.intf.data._range)+1

    # Queue up random messages onto the different drivers
    msg_a = [randint(0, (1 << intf_size) - 1) for _ in range(randint(50, 100))]
    msg_b = [randint(0, (1 << intf_size) - 1) for _ in range(randint(50, 100))]

    for msg in msg_a: dut.stream_a.append((msg, 0))
    for msg in msg_b: dut.stream_b.append((msg, 0))

    # Construct the expected arbitration using the active scheme
    arb_scheme = dut.dut.dut.ARB_SCHEME.value.decode("utf-8")
    last       = 0
    while msg_a or msg_b:
        active = None
        if arb_scheme == "round_robin":
            for idx in range(2):
                active = (idx + last + 1) % 2
                if   active == 0 and msg_a: dut.expected.append((msg_a.pop(0), 0))
                elif active == 1 and msg_b: dut.expected.append((msg_b.pop(0), 0))
        elif arb_scheme == "prefer_a":
            if   msg_a: dut.expected.append((msg_a.pop(0), 0))
            elif msg_b: dut.expected.append((msg_b.pop(0), 0))
        elif arb_scheme == "prefer_b":
            if   msg_b: dut.expected.append((msg_b.pop(0), 0))
            elif msg_a: dut.expected.append((msg_a.pop(0), 0))
        else:
            raise Exception(f"Unknown arbitration scheme: {arb_scheme}")
        # Capture the last selection
        if active != None: last = active

factory = TestFactory(multi_dir)
factory.add_option("backpressure", [True, False])
factory.generate_tests()
