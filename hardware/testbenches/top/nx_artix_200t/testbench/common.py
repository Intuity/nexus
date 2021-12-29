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

from cocotb.triggers import RisingEdge

from drivers.axi4stream.common import AXI4StreamTransaction
from nxconstants import ControlReqType, ControlRespType, ControlRequest, ControlResponse

def to_bytes(data, bits):
    return bytearray([((data >> (x * 8)) & 0xFF) for x in range(int(ceil(bits / 8)))])

async def trigger(dut, active=0, col_mask=None, cycles=0):
    """ Trigger the mesh to run for N cycles """
    if col_mask is None:
        col_mask = (1 << int(dut.COLUMNS)) - 1
    req                  = ControlRequest()
    req.trigger.command  = ControlReqType.TRIGGER
    req.trigger.col_mask = col_mask
    req.trigger.cycles   = cycles
    req.trigger.active   = active
    dut.inbound.append(AXI4StreamTransaction(data=to_bytes(req.pack(), 128)))
    await dut.inbound.idle()

async def check_status(
    dut, active=0, mesh_idle=1, agg_idle=1, seen_low=0, first_tick=1, cycle=0,
    countdown=0,
):
    """ Check the current status of the mesh """
    # Generate and queue request
    req             = ControlRequest()
    req.raw.command = ControlReqType.READ_STATUS
    dut.inbound.append(AXI4StreamTransaction(data=to_bytes(req.pack(), 128)))
    # Generate and queue response
    resp                   = ControlResponse()
    resp.status.format     = ControlRespType.STATUS
    resp.status.active     = active
    resp.status.mesh_idle  = mesh_idle
    resp.status.agg_idle   = agg_idle
    resp.status.seen_low   = seen_low
    resp.status.first_tick = first_tick
    resp.status.cycle      = cycle
    resp.status.countdown  = countdown
    dut.expected.append(AXI4StreamTransaction(data=to_bytes(resp.pack(), 128)))
    # Wait for response to be checked
    while dut.expected: await RisingEdge(dut.clk)

async def request_reset(dut):
    """ Request a soft reset """
    # Generate and queue request
    req             = ControlRequest()
    req.raw.command = ControlReqType.SOFT_RESET
    dut.inbound.append(AXI4StreamTransaction(data=to_bytes(req.pack(), 128)))
    await dut.inbound.idle()
    # Wait for internal reset to rise
    while dut.dut.u_dut.u_nexus.rst_internal == 0: await RisingEdge(dut.clk)
    # Wait for internal reset to fall
    while dut.dut.u_dut.u_nexus.rst_internal == 1: await RisingEdge(dut.clk)