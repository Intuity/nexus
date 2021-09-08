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

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from nxconstants import ControlCommand, ControlRaw, ControlSetActive

from ..testbench import testcase

def status(active, idle_low, first_tick, interval_set):
    enc  = (active       & 0x1) << 3
    enc |= (idle_low     & 0x1) << 2
    enc |= (first_tick   & 0x1) << 1
    enc |= (interval_set & 0x1) << 0
    return enc

@testcase()
async def set_active(dut):
    """ Read the device parameters """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Monitor for trigger pulses
    triggered = 0
    async def count_triggers():
        nonlocal triggered
        while True:
            await RisingEdge(dut.clk)
            if dut.mesh_trigger_o == 1:
                triggered += 1
    cocotb.fork(count_triggers())

    # Request the initial state
    dut.info("Checking initial state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append((status(0, 0, 1, 0), 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Request the initial cycle count
    dut.info("Checking initial cycle count")
    dut.inbound.append(ControlRaw(command=ControlCommand.CYCLES).pack())
    dut.expected.append((0, 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Check outputs from control
    assert triggered            == 0
    assert dut.status_active_o  == 0
    assert dut.status_idle_o    == 1
    assert dut.status_trigger_o == 0
    assert dut.mesh_trigger_o   == 0
    assert dut.token_grant_o    == 0

    # Bounce idle (as if we were loading up a design)
    dut.mesh_idle_i <= 0
    await RisingEdge(dut.clk)
    dut.mesh_idle_i <= 1
    await RisingEdge(dut.clk)

    # Request the updated state
    dut.info("Checking updated state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append((status(0, 1, 1, 0), 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Set the mesh to be active
    dut.info("Activating mesh")
    dut.inbound.append(ControlSetActive(command=ControlCommand.ACTIVE, active=1).pack())
    await dut.inbound.idle()
    await ClockCycles(dut.clk, 10)

    # Check trigger has fired once
    assert triggered == 1, f"Expected 1 trigger, got {triggered}"

    # Request the active state
    dut.info("Checking active state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append((status(1, 0, 0, 0), 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Request the first cycle count
    dut.info("Checking first cycle count")
    dut.inbound.append(ControlRaw(command=ControlCommand.CYCLES).pack())
    dut.expected.append((1, 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Cycle idle a few times
    num_cycles = randint(5, 20)
    dut.info(f"Running for {num_cycles} cycles")
    for _ in range(num_cycles):
        dut.mesh_idle_i <= 0
        await ClockCycles(dut.clk, randint(10, 20))
        dut.mesh_idle_i <= 1
        await ClockCycles(dut.clk, randint(1, 5))

    # Wait a few cycles to settle
    await ClockCycles(dut.clk, 10)

    # Check the number of triggers
    assert triggered == (1 + num_cycles), \
        f"Expecting {1 + num_cycles} triggers, got {triggered}"

    # Request the active state
    dut.info("Checking active state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append((status(1, 0, 0, 0), 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Request the updated cycle count
    dut.info("Checking updated cycle count")
    dut.inbound.append(ControlRaw(command=ControlCommand.CYCLES).pack())
    dut.expected.append((1 + num_cycles, 0))
    while dut.expected: await RisingEdge(dut.clk)
