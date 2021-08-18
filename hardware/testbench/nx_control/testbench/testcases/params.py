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

from nx_constants import ControlParameter
from nx_control import build_req_param

from ..testbench import testcase

@testcase()
async def read_params(dut):
    """ Read the device parameters """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Create a lookup between parameter and the true value
    lookup = {
        ControlParameter.COUNTER_WIDTH : int(dut.dut.dut.TX_PYLD_WIDTH),
        ControlParameter.ROWS          : int(dut.dut.dut.ROWS         ),
        ControlParameter.COLUMNS       : int(dut.dut.dut.COLUMNS      ),
        ControlParameter.NODE_INPUTS   : int(dut.dut.dut.INPUTS       ),
        ControlParameter.NODE_OUTPUTS  : int(dut.dut.dut.OUTPUTS      ),
        ControlParameter.NODE_REGISTERS: int(dut.dut.dut.REGISTERS    ),
    }

    # Request all parameters in a random order
    for param in sorted(list(ControlParameter), key=lambda _: random()):
        dut.info(f"Requesting parameter {ControlParameter(param).name}")
        dut.inbound.append(build_req_param(int(param)))
        dut.expected.append((lookup[param], 0))
