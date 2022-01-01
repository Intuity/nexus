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
from random import choice, randint

from cocotb.regression import TestFactory
from cocotb.handle import Force, Release
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.axi4stream.common import AXI4StreamTransaction
from nxconstants import (ControlReqType, ControlRespType, ControlRequest,
                         ControlResponse, HW_DEV_ID, HW_VER_MAJOR,
                         HW_VER_MINOR, TIMER_WIDTH)

from ..common import check_status, request_reset, to_bytes, trigger
from ..testbench import testcase

async def control(dut, backpressure):
    """ Read back parameters and status from the controller """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Enable/disable backpressure
    dut.outbound.delays = backpressure

    # Build a parameter request and expected response
    req_param             = ControlRequest()
    req_param.raw.command = ControlReqType.READ_PARAMS
    req_param             = req_param.raw.pack()

    resp_param                    = ControlResponse()
    resp_param.params.format      = ControlRespType.PARAMS
    resp_param.params.id          = HW_DEV_ID
    resp_param.params.ver_major   = HW_VER_MAJOR
    resp_param.params.ver_minor   = HW_VER_MINOR
    resp_param.params.timer_width = TIMER_WIDTH
    resp_param.params.rows        = int(dut.dut.u_dut.u_nexus.ROWS)
    resp_param.params.columns     = int(dut.dut.u_dut.u_nexus.COLUMNS)
    resp_param.params.node_ins    = int(dut.dut.u_dut.u_nexus.INPUTS)
    resp_param.params.node_outs   = int(dut.dut.u_dut.u_nexus.OUTPUTS)
    resp_param.params.node_regs   = int(dut.dut.u_dut.u_nexus.REGISTERS)
    resp_param                    = resp_param.params.pack()

    # Build a status request and expected response
    req_status             = ControlRequest()
    req_status.raw.command = ControlReqType.READ_STATUS
    req_status             = req_status.raw.pack()

    resp_status                   = ControlResponse()
    resp_status.status.format     = ControlRespType.STATUS
    resp_status.status.active     = 0
    resp_status.status.mesh_idle  = 1
    resp_status.status.agg_idle   = 1
    resp_status.status.seen_low   = 1
    resp_status.status.first_tick = 1
    resp_status.status.cycle      = 0
    resp_status.status.countdown  = 0
    resp_status                   = resp_status.status.pack()

    # Run a number of iterations
    for _ in range(100):
        name, req, resp = choice((
            ("PARAM",  req_param,  resp_param),
            ("STATUS", req_status, resp_status)
        ))
        dut.inbound.append(AXI4StreamTransaction(data=to_bytes(req, 128)))
        dut.expected.append(AXI4StreamTransaction(data=to_bytes(resp, 128)))
        await dut.inbound.idle()

factory = TestFactory(control)
factory.add_option("backpressure", [True, False])
factory.generate_tests()

@testcase()
async def soft_reset(dut):
    """ Trigger a soft reset and check the interval is cleared """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Apply force to mesh idles to stop them from falling
    ctrl = dut.dut.u_dut.u_nexus.u_control
    ctrl.i_mesh_node_idle <= Force((1 << int(dut.COLUMNS)) - 1)
    ctrl.i_mesh_agg_idle  <= Force(1)

    # Check the initial state
    dut.info("Checking initial state")
    await check_status(
        dut, active=0, mesh_idle=1, agg_idle=1, seen_low=1, first_tick=1,
        cycle=0, countdown=0,
    )

    # Trigger the mesh with a given interval
    interval = randint(1, 1000)
    dut.info(f"Activating mesh for {interval} cycles")
    await trigger(dut, active=1, cycles=interval)

    # Check the status
    dut.info("Checking status")
    await check_status(
        dut, active=1, mesh_idle=1, agg_idle=1, seen_low=0, first_tick=0,
        cycle=0, countdown=(interval - 1),
    )

    # Trigger a soft reset
    dut.info("Triggering soft reset")
    await request_reset(dut)

    # Read back the status to check an interval has been cleared
    # NOTE: 'seen_low' is zero here because the forces are applied
    dut.info("Checking state after reset")
    await check_status(
        dut, active=0, mesh_idle=1, agg_idle=1, seen_low=0, first_tick=1,
        cycle=0, countdown=0,
    )

    # Release forces
    ctrl.i_mesh_node_idle <= Release()
    ctrl.i_mesh_agg_idle  <= Release()
