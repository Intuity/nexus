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

from cocotb.triggers import ClockCycles, First, RisingEdge

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
async def fetching(dut):
    """ Test that the DUT will fetch the right number of instructions """
    dut.info("Resetting DUT")
    await dut.reset()

    # Without populating instructions, try triggering execution
    dut.trigger <= 1
    await RisingEdge(dut.clk)
    dut.trigger <= 0

    # Check DUT remains idle for 100 cycles
    for _ in range(100):
        assert dut.idle == 1, "DUT did not remain idle"
        await RisingEdge(dut.clk)

    # Check that no instruction fetches occurred
    assert dut.ram.stats.reads == 0, "No reads from RAM should have occurred"

    # Randomise fetching of different numbers of instructions
    last = 0
    for _ in range(10):
        # Setup a random number of populated instructions
        populated = randint(10, 100)
        dut.populated <= populated
        await RisingEdge(dut.clk)

        # Check still idle
        assert dut.idle == 1, "DUT not idle"

        # Trigger execution
        dut.trigger <= 1
        await RisingEdge(dut.clk)
        dut.trigger <= 0
        await RisingEdge(dut.clk)
        assert dut.idle == 0, "DUT is still idle"

        # Wait until the DUT goes idle again
        while dut.idle == 0: await RisingEdge(dut.clk)
        assert dut.idle == 1, "DUT is not idle"

        # Check fetch delta
        rcvd  = dut.ram.stats.reads
        delta = rcvd - last
        assert delta == populated, f"Expected {populated} fetches, got {delta}"

        # Update the last monitor count
        last = rcvd

@testcase()
async def restart(dut):
    """ Restart execution and check that instruction fetch restarts """
    dut.info("Resetting DUT")
    await dut.reset()

    # Randomise fetching of different numbers of instructions
    last = 0
    for _ in range(10):
        # Setup a random number of populated instructions
        populated = randint(50, 100)
        dut.populated <= populated
        await RisingEdge(dut.clk)

        # Check still idle
        assert dut.idle == 1, "DUT not idle"

        # Trigger execution
        dut.trigger <= 1
        await RisingEdge(dut.clk)
        dut.trigger <= 0
        await RisingEdge(dut.clk)
        assert dut.idle == 0, "DUT is still idle"

        # Wait for some fetches to occur
        dut.info("Waiting for some of fetches to occur")
        while (dut.ram.stats.reads - last) < randint(
            int(0.1 * populated), int(0.9 * populated)
        ): await RisingEdge(dut.clk)

        # Check DUT is still active
        assert dut.idle == 0, "DUT is not active"

        # Restart execution
        dut.info("Restarting execution")
        dut.trigger <= 1
        await RisingEdge(dut.clk)
        dut.trigger <= 0
        await RisingEdge(dut.clk)
        assert dut.idle == 0, "DUT is still idle"

        # Wait until the DUT goes idle again
        while dut.idle == 0: await RisingEdge(dut.clk)
        assert dut.idle == 1, "DUT is not idle"

        # Check fetch delta
        rcvd  = dut.ram.stats.reads
        delta = rcvd - last
        exp   = populated * 2
        assert delta == exp, f"Expected ~{exp} fetches, got {delta}"

        # Check instruction fetches
        assert dut.ram.stats.last_read == (populated - 1), \
            f"Last fetch 0x{dut.ram.stats.last_read:08X} != expected 0x{populated-1:08X}"

        # Update the last monitor count
        last = rcvd
