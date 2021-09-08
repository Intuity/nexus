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

from nxconstants import ControlCommand, ControlReadParam, ControlParam

from ..testbench import testcase

@testcase()
async def read_params(dut):
    """ Read the device parameters """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Create a lookup between parameter and the true value
    lookup = {
        ControlParam.COUNTER_WIDTH : int(dut.dut.dut.TX_PYLD_WIDTH),
        ControlParam.ROWS          : int(dut.dut.dut.ROWS         ),
        ControlParam.COLUMNS       : int(dut.dut.dut.COLUMNS      ),
        ControlParam.NODE_INPUTS   : int(dut.dut.dut.INPUTS       ),
        ControlParam.NODE_OUTPUTS  : int(dut.dut.dut.OUTPUTS      ),
        ControlParam.NODE_REGISTERS: int(dut.dut.dut.REGISTERS    ),
    }

    # Request all parameters in a random order
    for param in sorted(list(ControlParam), key=lambda _: random()):
        dut.info(f"Requesting parameter {ControlParam(param).name}")
        dut.inbound.append(ControlReadParam(command=ControlCommand.PARAM, param=param).pack())
        dut.expected.append((lookup[param], 0))
