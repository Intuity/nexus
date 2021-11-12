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
async def set_interval(dut):
    """ Read the device parameters """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Monitor for trigger pulses
    triggered = 0
    async def fake_mesh():
        nonlocal triggered
        while True:
            await RisingEdge(dut.clk)
            if dut.mesh_trigger == ((1 << int(dut.dut.COLUMNS)) - 1):
                triggered += 1
                dut.mesh_idle <= 0
                await ClockCycles(dut.clk, randint(10, 20))
                dut.mesh_idle <= ((1 << int(dut.dut.COLUMNS)) - 1)
    cocotb.fork(fake_mesh())

    # Request the initial state
    dut.info("Checking initial state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append(StreamTransaction(ControlStatus(
        idle_low=1, first_tick=1
    ).pack()))
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
    dut.expected.append(StreamTransaction(ControlStatus(
        idle_low=1, first_tick=1
    ).pack()))
    while dut.expected: await RisingEdge(dut.clk)

    # Setup an interval
    dut.info("Setting an interval")
    cycles = randint(10, 20)
    dut.inbound.append(ControlRaw(command=ControlCommand.INTERVAL, payload=cycles).pack())

    # Request the updated state
    dut.info("Checking updated state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append(StreamTransaction(ControlStatus(
        idle_low=1, first_tick=1, interval_set=1
    ).pack()))
    while dut.expected: await RisingEdge(dut.clk)

    # Set the mesh to be active
    dut.info("Activating mesh")
    dut.inbound.append(ControlSetActive(command=ControlCommand.ACTIVE, active=1).pack())
    await dut.inbound.idle()

    # Wait until active signal clears
    dut.info("Waiting for active signal to clear")
    while int(dut.status.active) == 0: await RisingEdge(dut.clk)
    while int(dut.status.active) == 1: await RisingEdge(dut.clk)

    # Request the state
    dut.info("Checking state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append(StreamTransaction(ControlStatus(
        idle_low=1, interval_set=1
    ).pack()))
    while dut.expected: await RisingEdge(dut.clk)

    # Request the updated cycle count
    dut.info("Checking updated cycle count")
    dut.inbound.append(ControlRaw(command=ControlCommand.CYCLES).pack())
    dut.expected.append(StreamTransaction(cycles))
    while dut.expected: await RisingEdge(dut.clk)

    # Setup an interval
    dut.info("Clearing the interval")
    dut.inbound.append(ControlRaw(command=ControlCommand.INTERVAL, payload=0).pack())

    # Request the state
    dut.info("Checking state")
    dut.inbound.append(ControlRaw(command=ControlCommand.STATUS).pack())
    dut.expected.append(StreamTransaction(ControlStatus(idle_low=1).pack()))
    while dut.expected: await RisingEdge(dut.clk)
