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

from nx_control import (build_req_status, build_set_active, build_req_cycles,
                        build_set_interval)

from ..testbench import testcase

def status(active, idle_low, first_tick, interval_set):
    enc  = (active       & 0x1) << 3
    enc |= (idle_low     & 0x1) << 2
    enc |= (first_tick   & 0x1) << 1
    enc |= (interval_set & 0x1) << 0
    return enc

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
            if dut.mesh_trigger_o == 1:
                triggered += 1
                dut.mesh_idle_i <= 0
                await ClockCycles(dut.clk, randint(10, 20))
                dut.mesh_idle_i <= 1
    cocotb.fork(fake_mesh())

    # Request the initial state
    dut.info("Checking initial state")
    dut.inbound.append(build_req_status())
    dut.expected.append((status(0, 0, 1, 0), 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Request the initial cycle count
    dut.info("Checking initial cycle count")
    dut.inbound.append(build_req_cycles())
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
    dut.inbound.append(build_req_status())
    dut.expected.append((status(0, 1, 1, 0), 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Setup an interval
    dut.info("Setting an interval")
    cycles = randint(10, 20)
    dut.inbound.append(build_set_interval(cycles))

    # Request the updated state
    dut.info("Checking updated state")
    dut.inbound.append(build_req_status())
    dut.expected.append((status(0, 1, 1, 1), 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Set the mesh to be active
    dut.info("Activating mesh")
    dut.inbound.append(build_set_active(1))
    await dut.inbound.idle()

    # Wait until active signal clears
    dut.info("Waiting for active signal to clear")
    while int(dut.status_active_o) == 0: await RisingEdge(dut.clk)
    while int(dut.status_active_o) == 1: await RisingEdge(dut.clk)

    # Request the state
    dut.info("Checking state")
    dut.inbound.append(build_req_status())
    dut.expected.append((status(0, 1, 0, 0), 0))
    while dut.expected: await RisingEdge(dut.clk)

    # Request the updated cycle count
    dut.info("Checking updated cycle count")
    dut.inbound.append(build_req_cycles())
    dut.expected.append((cycles, 0))
    while dut.expected: await RisingEdge(dut.clk)
