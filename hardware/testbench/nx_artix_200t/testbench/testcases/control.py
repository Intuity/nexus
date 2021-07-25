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

    # Collect responses
    responses = []

    # Request the device identifier
    dut.info("Requesting device ID and version")
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_req_id(), 31
    )))
    responses.append(DEVICE_ID)
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_req_version(), 31
    )))
    responses.append((DEVICE_VERSION_MAJOR << 8) | DEVICE_VERSION_MINOR)

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
        dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
            (1 << 31) | build_req_param(int(param)), 32
        )))
        responses.append(exp_val)

    # Request the device status
    dut.info("Requesting device status")
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_req_status(), 31
    )))
    responses.append(
        (0 << 3) | # ACTIVE       =0 -> inactive
        (1 << 2) | # SEEN_IDLE_LOW=1 -> idle has been observed low
        (1 << 1) | # FIRST_TICK   =1 -> fresh from reset
        (0 << 0)   # INTERVAL_SET =0 -> no interval has been set
    )

    # Generate an AXI4-Stream of responses
    all_bytes = bytearray([])
    for chunk in responses:
        all_bytes += to_bytes((1 << 31) | chunk, 32)

    # Pad out to an integer number of 128-bit chunks
    if len(all_bytes) % 16 > 0:
        all_bytes += bytearray([0] * (16 - (len(all_bytes) % 16)))

    dut.exp_ctrl.append(AXI4StreamTransaction(data=all_bytes))
