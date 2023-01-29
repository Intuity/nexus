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
from math import ceil

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.stream.common import StreamTransaction
from nxconstants import ControlReqType, ControlRequest

from ..common import trigger, check_status
from ..testbench import testcase

@testcase()
async def soft_reset(dut):
    """ Request a soft reset from the device """
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

    # Check the initial state
    dut.info("Checking initial state")
    await check_status(
        dut, active=0, mesh_idle=1, agg_idle=1, seen_low=0, first_tick=1,
        cycle=0, countdown=0,
    )

    # Check outputs from control
    assert triggered          == 0
    assert dut.soft_reset     == 0
    assert dut.status.active  == 0
    assert dut.status.idle    == 1
    assert dut.status.trigger == 0
    assert dut.mesh_trigger   == 0

    # Bounce idle (as if we were loading up a design)
    dut.node_idle <= 0
    await RisingEdge(dut.clk)
    dut.node_idle <= ((1 << int(dut.dut.COLUMNS)) - 1)
    await RisingEdge(dut.clk)

    # Request the updated state
    dut.info("Checking updated state")
    await check_status(
        dut, active=0, mesh_idle=1, agg_idle=1, seen_low=1, first_tick=1,
        cycle=0, countdown=0,
    )

    # Set the mesh to be active
    dut.info("Activating mesh")
    await trigger(dut, active=1, cycles=0)
    await ClockCycles(dut.clk, 10)

    # Check trigger has fired once
    assert triggered == 1, f"Expected 1 trigger, got {triggered}"

    # Request the active state
    dut.info("Checking active state")
    await check_status(
        dut, active=1, mesh_idle=1, agg_idle=1, seen_low=0, first_tick=0,
        cycle=0, countdown=0,
    )

    # Trigger a soft reset
    req             = ControlRequest()
    req.raw.command = ControlReqType.SOFT_RESET
    req.raw.payload = 1
    dut.ctrl_in.append(StreamTransaction(req.pack()))
    await dut.ctrl_in.idle()
    await ClockCycles(dut.clk, 10)

    # Check soft reset is asserted
    assert dut.soft_reset == 1
