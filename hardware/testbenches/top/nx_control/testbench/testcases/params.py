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

from random import random

from drivers.stream.common import StreamTransaction
from nxconstants import (ControlCommand, ControlReadParam, ControlParam,
                         HW_DEV_ID, MESSAGE_WIDTH, HW_VER_MAJOR, HW_VER_MINOR)

from ..testbench import testcase

@testcase()
async def read_params(dut):
    """ Read the device parameters """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Create a lookup between parameter and the true value
    lookup = {
        ControlParam.ID            : HW_DEV_ID,
        ControlParam.VERSION       : (HW_VER_MAJOR << 8) | HW_VER_MINOR,
        ControlParam.COUNTER_WIDTH : MESSAGE_WIDTH,
        ControlParam.ROWS          : int(dut.ROWS     ),
        ControlParam.COLUMNS       : int(dut.COLUMNS  ),
        ControlParam.NODE_INPUTS   : int(dut.INPUTS   ),
        ControlParam.NODE_OUTPUTS  : int(dut.OUTPUTS  ),
        ControlParam.NODE_REGISTERS: int(dut.REGISTERS),
    }

    # Request all parameters in a random order
    for param in sorted(list(ControlParam), key=lambda _: random()):
        dut.info(f"Requesting parameter {ControlParam(param).name}")
        dut.inbound.append(ControlReadParam(command=ControlCommand.PARAM, param=param).pack())
        dut.expected.append(StreamTransaction(lookup[param]))
