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
    dut.trigger_i <= 1
    await RisingEdge(dut.clk)
    dut.trigger_i <= 0

    # Check DUT remains idle for 100 cycles
    for _ in range(100):
        assert dut.idle_o == 1, "DUT did not remain idle"
        await RisingEdge(dut.clk)

    # Check that no instruction fetches occurred
    assert dut.instr_store.stats.received_transactions == 0, \
        "Instruction store should not have received any transactions"

    # Randomise fetching of different numbers of instructions
    last = 0
    for _ in range(10):
        # Setup a random number of populated instructions
        populated = randint(10, 100)
        dut.populated_i <= populated
        await RisingEdge(dut.clk)

        # Check still idle
        assert dut.idle_o == 1, "DUT not idle"

        # Trigger execution
        dut.trigger_i <= 1
        await RisingEdge(dut.clk)
        dut.trigger_i <= 0
        await RisingEdge(dut.clk)
        assert dut.idle_o == 0, "DUT is still idle"

        # Wait until the DUT goes idle again
        await First(ClockCycles(dut.clk, 1000), RisingEdge(dut.idle_o))
        await RisingEdge(dut.clk)
        assert dut.idle_o == 1, "DUT is not idle"

        # Check fetch delta
        rcvd  = dut.instr_store.stats.received_transactions
        delta = rcvd - last
        assert delta == populated, f"Expected {populated} fetches, got {delta}"

        # Check that the received transactions correctly increment
        for idx in range(populated):
            item = dut.instr_store._recvQ.popleft()
            assert item.address == idx, f"Item {idx} has address {item.address}"

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
        dut.populated_i <= populated
        await RisingEdge(dut.clk)

        # Check still idle
        assert dut.idle_o == 1, "DUT not idle"

        # Trigger execution
        dut.trigger_i <= 1
        await RisingEdge(dut.clk)
        dut.trigger_i <= 0
        await RisingEdge(dut.clk)
        assert dut.idle_o == 0, "DUT is still idle"

        # Wait for some fetches to occur
        dut.info("Waiting for some of fetches to occur")
        while (dut.instr_store.stats.received_transactions - last) < randint(
            int(0.1 * populated), int(0.9 * populated)
        ): await RisingEdge(dut.clk)

        # Check DUT is still active
        assert dut.idle_o == 0, "DUT is not active"

        # Restart execution
        dut.info("Restarting execution")
        dut.trigger_i <= 1
        await RisingEdge(dut.clk)
        dut.trigger_i <= 0
        await RisingEdge(dut.clk)
        assert dut.idle_o == 0, "DUT is still idle"

        # Wait until the DUT goes idle again
        await First(ClockCycles(dut.clk, 1000), RisingEdge(dut.idle_o))
        await RisingEdge(dut.clk)
        assert dut.idle_o == 1, "DUT is not idle"

        # Check fetch delta
        rcvd  = dut.instr_store.stats.received_transactions
        delta = rcvd - last
        exp   = populated * 2
        assert delta == exp, f"Expected ~{exp} fetches, got {delta}"

        # Check instruction fetches
        seq  = [x for x in range(delta - populated)]
        seq += [x for x in range(populated)]
        for idx, addr in enumerate(seq):
            item = dut.instr_store._recvQ.popleft()
            assert item.address == addr, \
                f"Item {idx} expecting address {addr}, got {item.address}"

        # Update the last monitor count
        last = rcvd
