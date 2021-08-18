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

from hardware.testbench.common.nx_control import build_set_interval
from math import ceil
from random import random, randint

from cocotb.regression import TestFactory
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.axi4stream.common import AXI4StreamTransaction
from nx_constants import (ControlParameter, DEVICE_ID, DEVICE_VERSION_MAJOR,
                          DEVICE_VERSION_MINOR)
from nx_control import (build_req_id, build_req_version, build_req_param,
                        build_req_status, build_set_interval, build_soft_reset)

from ..testbench import testcase

def to_bytes(data, bits):
    return bytearray([((data >> (x * 8)) & 0xFF) for x in range(int(ceil(bits / 8)))])

async def control(dut, backpressure):
    """ Issue control block requests and collect responses """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Enable/disable backpressure
    dut.ob_ctrl.delays = backpressure

    # Build requests and expected responses
    req_resp = [
        # Device ID
        (build_req_id(), DEVICE_ID),
        # Version
        (build_req_version(), (DEVICE_VERSION_MAJOR << 8) | DEVICE_VERSION_MINOR),
        # Parameters
        # - Counter Width
        (
            build_req_param(int(ControlParameter.COUNTER_WIDTH)),
            int(dut.dut.dut.core.control.TX_PYLD_WIDTH)
        ),
        # - Rows
        (
            build_req_param(int(ControlParameter.ROWS)),
            int(dut.dut.dut.core.control.ROWS)
        ),
        # - Columns
        (
            build_req_param(int(ControlParameter.COLUMNS)),
            int(dut.dut.dut.core.control.COLUMNS)
        ),
        # - Node_inputs
        (
            build_req_param(int(ControlParameter.NODE_INPUTS)),
            int(dut.dut.dut.core.control.INPUTS)
        ),
        # - Node_outputs
        (
            build_req_param(int(ControlParameter.NODE_OUTPUTS)),
            int(dut.dut.dut.core.control.OUTPUTS)
        ),
        # - Node_registers
        (
            build_req_param(int(ControlParameter.NODE_REGISTERS)),
            int(dut.dut.dut.core.control.REGISTERS)
        ),
        # Device status
        (
            build_req_status(), (
                (0 << 3) | # ACTIVE       =0 -> inactive
                (1 << 2) | # SEEN_IDLE_LOW=1 -> idle has been observed low
                (1 << 1) | # FIRST_TICK   =1 -> fresh from reset
                (0 << 0)   # INTERVAL_SET =0 -> no interval has been set
            )
        ),
    ]

    # Run many iterations
    for idx in range(100):
        if (idx % 10) == 0: dut.info(f"Running iteration {idx}")
        # Choose the requests to send
        chosen = sorted(req_resp, key=lambda _: random())[:randint(1, len(req_resp))]
        # Send all of the requests and build expected responses
        resp_bytes = bytearray([])
        for req, resp in chosen:
            dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes((1 << 31) | req, 31)))
            resp_bytes += to_bytes((1 << 31) | resp, 32)
        # Pad to the nearest 16 bytes
        if len(resp_bytes) % 16 != 0:
            resp_bytes += bytearray([0] * (16 - (len(resp_bytes) % 16)))
        # Queue the expected response
        dut.exp_ctrl.append(AXI4StreamTransaction(data=resp_bytes))
        # Wait for responses to drain
        while dut.exp_ctrl: await RisingEdge(dut.clk)
        await ClockCycles(dut.clk, 10)

factory = TestFactory(control)
factory.add_option("backpressure", [True, False])
factory.generate_tests()

@testcase()
async def soft_reset(dut):
    """ Trigger a soft reset and check the interval is cleared """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Set the interval to a non-zero value
    interval = randint(1, 1000)
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_set_interval(interval), 32
    )))

    # Read back the status to check an interval has been set
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_req_status(), 32
    )))
    dut.exp_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | (
            (0 << 3) | # ACTIVE       =0 -> inactive
            (1 << 2) | # SEEN_IDLE_LOW=1 -> idle has been observed low
            (1 << 1) | # FIRST_TICK   =1 -> fresh from reset
            (1 << 0)   # INTERVAL_SET =1 -> an interval has been set
        ), 128
    )))

    # Wait for response
    while dut.exp_ctrl: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Trigger a soft reset
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_soft_reset(), 32
    )))

    dut.info("Waiting for internal reset to rise")
    while dut.dut.dut.core.rst_internal == 0: await RisingEdge(dut.clk)
    dut.info("Waiting for internal reset to fall")
    while dut.dut.dut.core.rst_internal == 1: await RisingEdge(dut.clk)

    # Read back the status to check an interval has been cleared
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | build_req_status(), 32
    )))
    dut.exp_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | (
            (0 << 3) | # ACTIVE       =0 -> inactive
            (1 << 2) | # SEEN_IDLE_LOW=1 -> idle has been observed low
            (1 << 1) | # FIRST_TICK   =1 -> fresh from reset
            (0 << 0)   # INTERVAL_SET =0 -> no interval has been set
        ), 128
    )))
