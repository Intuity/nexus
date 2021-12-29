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
from math import ceil

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.stream.common import StreamTransaction
from nxconstants import ControlRespType, ControlResponse, OUT_BITS_PER_MSG

from ..common import trigger, check_status
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

    # Check the initial state
    dut.info("Checking initial state")
    await check_status(
        dut, active=0, mesh_idle=1, agg_idle=1, seen_low=0, first_tick=1,
        cycle=0, countdown=0,
    )

    # Check outputs from control
    assert triggered          == 0
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

    # Cycle idle a few times
    num_cycles = randint(5, 20)
    dut.info(f"Running for {num_cycles} cycles")
    for cycle in range(num_cycles):
        # Lower idle (faking mesh being busy)
        dut.node_idle <= 0
        dut.agg_idle  <= 0
        await ClockCycles(dut.clk, randint(10, 20))
        # Queue the output messages
        for idx in range(ceil(int(dut.COLUMNS) * int(dut.OUTPUTS) / OUT_BITS_PER_MSG)):
            resp                 = ControlResponse()
            resp.outputs.format  = ControlRespType.OUTPUTS
            resp.outputs.stamp   = cycle
            resp.outputs.index   = idx
            resp.outputs.section = 0
            dut.exp_ctrl.append(StreamTransaction(resp.pack()))
        # Raise idle (faking mesh completion)
        dut.node_idle <= ((1 << int(dut.dut.COLUMNS)) - 1)
        dut.agg_idle  <= 1
        # Wait for trigger
        while dut.mesh_trigger == 0: await RisingEdge(dut.clk)

    # Wait a few cycles to settle
    await ClockCycles(dut.clk, 10)

    # Check the number of triggers
    assert triggered == (1 + num_cycles), \
        f"Expecting {1 + num_cycles} triggers, got {triggered}"

    # Request the active state
    dut.info("Checking active state")
    await check_status(
        dut, active=1, mesh_idle=1, agg_idle=1, seen_low=0,
        first_tick=0, cycle=num_cycles, countdown=0,
    )
