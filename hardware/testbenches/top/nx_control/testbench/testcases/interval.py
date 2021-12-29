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

from math import ceil
from random import randint

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.stream.common import StreamTransaction
from nxconstants import ControlRespType, ControlResponse

from ..common import trigger, check_status
from ..testbench import testcase

@testcase()
async def set_interval(dut):
    """ Read the device parameters """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Monitor for trigger pulses
    en_mesh   = False
    triggered = 0
    async def fake_mesh():
        nonlocal triggered
        while True:
            await RisingEdge(dut.clk)
            if dut.mesh_trigger == ((1 << int(dut.dut.COLUMNS)) - 1):
                triggered += 1
                while not en_mesh: await RisingEdge(dut.clk)
                dut.node_idle <= 0
                dut.agg_idle  <= 0
                await ClockCycles(dut.clk, randint(10, 20))
                dut.node_idle <= ((1 << int(dut.dut.COLUMNS)) - 1)
                dut.agg_idle  <= 1
    cocotb.fork(fake_mesh())

    # Request the initial state
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

    # Run for an interval
    dut.info("Running for an interval")
    cycles = randint(10, 20)
    await trigger(dut, active=1, cycles=cycles)

    # Request the updated state
    dut.info("Checking updated state")
    await check_status(
        dut, active=1, mesh_idle=1, agg_idle=1, seen_low=0, first_tick=0,
        cycle=0, countdown=(cycles - 1),
    )

    # Allow the mesh to tick
    dut.info("Enabling dummy mesh")
    en_mesh = True

    # Queue up the output messages
    for cycle in range(cycles):
        for idx in range(ceil(int(dut.COLUMNS) * int(dut.OUTPUTS) / 96)):
            resp = ControlResponse()
            resp.outputs.format  = ControlRespType.OUTPUTS
            resp.outputs.stamp   = cycle
            resp.outputs.index   = idx
            resp.outputs.section = 0
            dut.exp_ctrl.append(StreamTransaction(resp.pack()))

    # Wait until active signal clears
    dut.info("Waiting for active signal to clear")
    while int(dut.status.active) == 0: await RisingEdge(dut.clk)
    while int(dut.status.active) == 1: await RisingEdge(dut.clk)

    # Request the state
    dut.info("Checking state")
    await check_status(
        dut, active=0, mesh_idle=1, agg_idle=1, seen_low=1, first_tick=0,
        cycle=cycles, countdown=0,
    )
