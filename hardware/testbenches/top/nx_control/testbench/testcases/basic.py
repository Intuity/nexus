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

from cocotb.triggers import ClockCycles

from drivers.stream.common import StreamTransaction
from nxconstants import (ControlCommand, ControlRaw, HW_DEV_ID, HW_VER_MAJOR,
                         HW_VER_MINOR)

from ..testbench import testcase

@testcase()
async def sanity(dut):
    """ Basic testcase """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Run for 100 clock cycles
    dut.info("Running for 100 clock cycles")
    await ClockCycles(dut.clk, 100)

    # All done!
    dut.info("Finished counting cycles")

@testcase()
async def read_id(dut):
    """ Read the device identifier """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Request the identifier
    dut.info("Requesting the identifier")
    dut.inbound.append(ControlRaw(command=ControlCommand.ID).pack())

    # Queue up expected response
    dut.expected.append(StreamTransaction(HW_DEV_ID))

@testcase()
async def read_version(dut):
    """ Read the device version information """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Request the identifier
    dut.info("Requesting the version")
    dut.inbound.append(ControlRaw(command=ControlCommand.VERSION).pack())

    # Queue up expected response
    dut.expected.append(StreamTransaction(
        HW_VER_MAJOR << 8 | HW_VER_MINOR << 0, 0
    ))

