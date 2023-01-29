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

from random import choice, randint

from cocotb.triggers import ClockCycles, RisingEdge

from drivers.stream.common import StreamTransaction
from nxconstants import (ControlReqType, ControlRespType, ControlRequest,
                         ControlResponse, NodeCommand, NodeMessage)

from ..testbench import testcase

@testcase()
async def routing(dut):
    """ Exercise message routing through the mesh """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Find the number of rows
    num_rows = int(dut.ROWS)
    num_cols = int(dut.COLUMNS)

    for _ in range(1000):
        # Keep randomising until it becomes a legal message
        msg = NodeMessage()
        while True:
            try:
                msg.unpack(randint(0, (1 << 31) - 1))
                break
            except Exception:
                continue

        # Set target outside of the fabric
        msg.raw.header.row    = num_rows
        msg.raw.header.column = randint(0, num_cols-1)

        # Don't use SIGNAL messages as aggregators will capture them
        msg.raw.header.command = choice([x for x in NodeCommand if x != NodeCommand.SIGNAL])

        # Create a message
        dut.debug(
            f"MSG - R: {msg.raw.header.row}, C: {msg.raw.header.column}, "
            f"CMD: {msg.raw.header.command} -> 0x{msg.pack():08X}"
        )

        # Forward the message into the mesh
        req                 = ControlRequest()
        req.to_mesh.command = ControlReqType.TO_MESH
        req.to_mesh.message = msg.pack()
        dut.ctrl_in.append(StreamTransaction(req.to_mesh.pack()))

        # Queue up the expected forwarded response
        resp                   = ControlResponse()
        resp.from_mesh.format  = ControlRespType.FROM_MESH
        resp.from_mesh.message = msg.pack()
        dut.expected.append(StreamTransaction(resp.from_mesh.pack()))

    # Wait for the mesh to go busy, then return to idle
    dut.info("Waiting for mesh to return to idle")
    while dut.status.idle == 1: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 100)
    while dut.status.idle == 0: await RisingEdge(dut.clk)
