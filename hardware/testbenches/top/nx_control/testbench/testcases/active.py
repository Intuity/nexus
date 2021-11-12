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

from drivers.stream.common import StreamTransaction
from nxconstants import ControlCommand, ControlRaw, ControlSetActive, ControlStatus

from ..testbench import testcase

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
            if dut.mesh_trigger == ((1 << int(dut.dut.COLUMNS)) - 1):
                triggered += 1
    cocotb.fork(count_triggers())

    # Request the initial state
    dut.info("Checking initial state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append(StreamTransaction(ControlStatus(idle_low=1, first_tick=1).pack()))
    while dut.expected: await RisingEdge(dut.clk)

    # Request the initial cycle count
    dut.info("Checking initial cycle count")
    dut.inbound.append(ControlRaw(command=ControlCommand.CYCLES).pack())
    dut.expected.append(StreamTransaction(0))
    while dut.expected: await RisingEdge(dut.clk)

    # Check outputs from control
    assert triggered          == 0
    assert dut.status.active  == 0
    assert dut.status.idle    == 1
    assert dut.status.trigger == 0
    assert dut.mesh_trigger   == 0

    # Bounce idle (as if we were loading up a design)
    dut.mesh_idle <= 0
    await RisingEdge(dut.clk)
    dut.mesh_idle <= ((1 << int(dut.dut.COLUMNS)) - 1)
    await RisingEdge(dut.clk)

    # Request the updated state
    dut.info("Checking updated state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append(StreamTransaction(ControlStatus(idle_low=1, first_tick=1).pack()))
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
    dut.expected.append(StreamTransaction(ControlStatus(active=1).pack()))
    while dut.expected: await RisingEdge(dut.clk)

    # Request the first cycle count
    dut.info("Checking first cycle count")
    dut.inbound.append(ControlRaw(command=ControlCommand.CYCLES).pack())
    dut.expected.append(StreamTransaction(1))
    while dut.expected: await RisingEdge(dut.clk)

    # Cycle idle a few times
    num_cycles = randint(5, 20)
    dut.info(f"Running for {num_cycles} cycles")
    for _ in range(num_cycles):
        dut.mesh_idle <= 0
        await ClockCycles(dut.clk, randint(10, 20))
        dut.mesh_idle <= ((1 << int(dut.dut.COLUMNS)) - 1)
        await ClockCycles(dut.clk, randint(1, 5))

    # Wait a few cycles to settle
    await ClockCycles(dut.clk, 10)

    # Check the number of triggers
    assert triggered == (1 + num_cycles), \
        f"Expecting {1 + num_cycles} triggers, got {triggered}"

    # Request the active state
    dut.info("Checking active state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append(StreamTransaction(ControlStatus(active=1).pack()))
    while dut.expected: await RisingEdge(dut.clk)

    # Request the updated cycle count
    dut.info("Checking updated cycle count")
    dut.inbound.append(ControlRaw(command=ControlCommand.CYCLES).pack())
    dut.expected.append(StreamTransaction(1 + num_cycles))
    while dut.expected: await RisingEdge(dut.clk)
