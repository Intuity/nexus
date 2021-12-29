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
async def outputs(dut):
    """ Exercise output message generation """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Pickup mesh parameters
    columns = int(dut.COLUMNS)
    nd_outs = int(dut.OUTPUTS)
    mh_outs = columns * nd_outs

    # Generate idle state updates and outputs
    async def fake_mesh():
        cycle = 0
        while True:
            await RisingEdge(dut.clk)
            if dut.mesh_trigger == ((1 << columns) - 1):
                # Lower the idle
                dut.node_idle <= 0
                dut.agg_idle  <= 0
                # Update the outputs a few times
                outputs = 0
                for _ in range(randint(10, 20)):
                    outputs           = randint(0, (1 << mh_outs) - 1)
                    dut.mesh_outputs <= outputs
                    await ClockCycles(dut.clk, randint(1, 5))
                # Queue up output messages using the final value
                for idx in range(ceil(mh_outs / 96)):
                    resp                 = ControlResponse()
                    resp.outputs.format  = ControlRespType.OUTPUTS
                    resp.outputs.stamp   = cycle
                    resp.outputs.index   = idx
                    resp.outputs.section = (outputs >> (idx * 96)) & ((1 << 96) - 1)
                    dut.exp_ctrl.append(StreamTransaction(resp.outputs.pack()))
                # Raise the idle
                dut.node_idle <= ((1 << columns) - 1)
                dut.agg_idle  <= 1
                # Increment the cycle counter
                cycle += 1
    cocotb.fork(fake_mesh())

    # Request the initial state
    dut.info("Checking initial state")
    await check_status(
        dut, active=0, mesh_idle=1, agg_idle=1, seen_low=0, first_tick=1,
        cycle=0, countdown=0,
    )

    # Run for an interval
    cycles = randint(100, 200)
    dut.info(f"Running for {cycles} cycles")
    await trigger(dut, active=1, cycles=cycles)

    # Wait for the mesh to return to idle
    while dut.status.active == 0: await RisingEdge(dut.clk)
    while dut.status.active == 1: await RisingEdge(dut.clk)

    # Check the state
    dut.info("Checking final state")
    await check_status(
        dut, active=0, mesh_idle=1, agg_idle=1, seen_low=1, first_tick=0,
        cycle=cycles, countdown=0,
    )
