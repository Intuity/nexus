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
from random import random

from cocotb.triggers import ClockCycles, RisingEdge

from drivers.axi4stream.common import AXI4StreamTransaction
from nx_constants import (ControlParameter, DEVICE_ID, DEVICE_VERSION_MAJOR,
                          DEVICE_VERSION_MINOR)
from nx_control import (build_req_id, build_req_version, build_req_param,
                        build_req_status)

from ..testbench import testcase

def to_bytes(data, bits):
    return bytearray([((data >> (x * 8)) & 0xFF) for x in range(int(ceil(bits / 8)))])

@testcase()
async def control(dut):
    """ Issue control block requests and collect responses """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Request the device identifier
    dut.info("Requesting device ID")
    dut.inbound.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_req_id(), 31
    )))
    dut.expected.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | DEVICE_ID, 32
    )))

    # Request the device version
    dut.info("Requesting device version")
    dut.inbound.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_req_version(), 31
    )))
    dut.expected.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | (DEVICE_VERSION_MAJOR << 8) | DEVICE_VERSION_MINOR, 32
    )))

    # Request the device parameters
    lookup = {
        ControlParameter.COUNTER_WIDTH : int(dut.dut.dut.core.control.PYLD_WIDTH),
        ControlParameter.ROWS          : int(dut.dut.dut.core.control.ROWS      ),
        ControlParameter.COLUMNS       : int(dut.dut.dut.core.control.COLUMNS   ),
        ControlParameter.NODE_INPUTS   : int(dut.dut.dut.core.control.INPUTS    ),
        ControlParameter.NODE_OUTPUTS  : int(dut.dut.dut.core.control.OUTPUTS   ),
        ControlParameter.NODE_REGISTERS: int(dut.dut.dut.core.control.REGISTERS ),
    }

    # Request all parameters in a random order
    for param, exp_val in sorted(list(lookup.items()), key=lambda _: random()):
        dut.info(f"Requesting parameter {param.name}")
        dut.inbound.append(AXI4StreamTransaction(data=to_bytes(
            (1 << 31) | build_req_param(int(param)), 32
        )))
        dut.expected.append(AXI4StreamTransaction(data=to_bytes(
            (1 << 31) | exp_val, 32
        )))

    # Request the device status
    dut.info("Requesting device status")
    dut.inbound.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_req_status(), 31
    )))
    dut.expected.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | (0 << 3) | (0 << 2) | (1 << 1) | (0 << 0), 32
    )))
