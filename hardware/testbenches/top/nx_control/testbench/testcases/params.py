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

from drivers.stream.common import StreamTransaction
from nxconstants import (ControlReqType, ControlRespType, ControlRequest,
                         ControlResponse, HW_DEV_ID, HW_VER_MAJOR, HW_VER_MINOR,
                         TIMER_WIDTH)

from ..testbench import testcase

@testcase()
async def read_params(dut):
    """ Read the device parameters """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Queue up a parameter request
    req             = ControlRequest()
    req.raw.command = ControlReqType.READ_PARAMS
    dut.ctrl_in.append(StreamTransaction(req.raw.pack()))

    # Queue up a parameter response
    resp                    = ControlResponse()
    resp.params.format      = ControlRespType.PARAMS
    resp.params.id          = HW_DEV_ID
    resp.params.ver_major   = HW_VER_MAJOR
    resp.params.ver_minor   = HW_VER_MINOR
    resp.params.timer_width = TIMER_WIDTH
    resp.params.rows        = int(dut.ROWS)
    resp.params.columns     = int(dut.COLUMNS)
    resp.params.node_ins    = int(dut.INPUTS)
    resp.params.node_outs   = int(dut.OUTPUTS)
    resp.params.node_regs   = int(dut.REGISTERS)
    dut.exp_ctrl.append(StreamTransaction(resp.params.pack()))
