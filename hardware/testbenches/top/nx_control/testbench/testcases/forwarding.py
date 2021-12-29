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

from drivers.stream.common import StreamTransaction
from nxconstants import (ControlReqType, ControlRequest, ControlRespType,
                         ControlResponse, MESSAGE_WIDTH)

from ..testbench import testcase

@testcase()
async def forwarding(dut):
    """ Forward messages to and from the mesh """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Queue up a whole bunch of messages to forward into the mesh
    for _ in range(randint(100, 1000)):
        # Generate the control request
        req                 = ControlRequest()
        req.to_mesh.command = ControlReqType.TO_MESH
        req.to_mesh.message = randint(0, (1 << MESSAGE_WIDTH) - 1)
        dut.ctrl_in.append(StreamTransaction(req.to_mesh.pack()))
        # Queue the expected message
        dut.exp_mesh.append(StreamTransaction(req.to_mesh.message))

    # Queue up a whole bunch of messages to forward out of the mesh
    for _ in range(randint(100, 1000)):
        # Generate the mesh message
        msg = randint(0, (1 << MESSAGE_WIDTH) - 1)
        dut.mesh_out.append(StreamTransaction(msg))
        # Queue the expected control response
        resp                   = ControlResponse()
        resp.from_mesh.format  = ControlRespType.FROM_MESH
        resp.from_mesh.message = msg
        dut.exp_ctrl.append(StreamTransaction(resp.from_mesh.pack()))

    # Log what was queued
    dut.info(f"Queued {len(dut.ctrl_in._sendQ)} messages to forward into mesh")
    dut.info(f"Queued {len(dut.mesh_out._sendQ)} messages to forward from mesh")
