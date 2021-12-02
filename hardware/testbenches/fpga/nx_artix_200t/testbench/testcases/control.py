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
from random import random, randint

from cocotb.regression import TestFactory
from cocotb.triggers import ClockCycles, RisingEdge

from drivers.axi4stream.common import AXI4StreamTransaction
import nxconstants
from nxconstants import (ControlCommand, ControlReadParam, ControlStatus,
                         ControlRaw, ControlParam, HW_DEV_ID, HW_VER_MAJOR,
                         HW_VER_MINOR)

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
        # Parameters
        # - Device ID
        (
            ControlReadParam(command=ControlCommand.PARAM, param=ControlParam.ID).pack(),
            HW_DEV_ID
        ),
        # - Version
        (
            ControlReadParam(command=ControlCommand.PARAM, param=ControlParam.VERSION).pack(),
            (HW_VER_MAJOR << 8) | HW_VER_MINOR
        ),
        # - Counter Width
        (
            ControlReadParam(command=ControlCommand.PARAM, param=ControlParam.COUNTER_WIDTH).pack(),
            int(dut.dut.u_dut.u_nexus.u_control.TX_PYLD_WIDTH)
        ),
        # - Rows
        (
            ControlReadParam(command=ControlCommand.PARAM, param=ControlParam.ROWS).pack(),
            int(dut.dut.u_dut.u_nexus.u_control.ROWS)
        ),
        # - Columns
        (
            ControlReadParam(command=ControlCommand.PARAM, param=ControlParam.COLUMNS).pack(),
            int(dut.dut.u_dut.u_nexus.u_control.COLUMNS)
        ),
        # - Node_inputs
        (
            ControlReadParam(command=ControlCommand.PARAM, param=ControlParam.NODE_INPUTS).pack(),
            int(dut.dut.u_dut.u_nexus.u_control.INPUTS)
        ),
        # - Node_outputs
        (
            ControlReadParam(command=ControlCommand.PARAM, param=ControlParam.NODE_OUTPUTS).pack(),
            int(dut.dut.u_dut.u_nexus.u_control.OUTPUTS)
        ),
        # - Node_registers
        (
            ControlReadParam(command=ControlCommand.PARAM, param=ControlParam.NODE_REGISTERS).pack(),
            int(dut.dut.u_dut.u_nexus.u_control.REGISTERS)
        ),
        # Device status
        (
            ControlRaw(command=ControlCommand.STATUS).pack(),
            ControlStatus(interval_set=0, first_tick=1, idle_low=1, active=0).pack()
        ),
    ]

    # Run many iterations
    for idx in range(100):
        if (idx % 10) == 0: dut.info(f"Running iteration {idx}")
        # Choose the requests to send
        chosen = sorted(req_resp, key=lambda _: random())[:randint(1, len(req_resp))]
        # Send all of the requests and build expected responses
        req_bytes  = bytearray([])
        resp_bytes = bytearray([])
        for req, resp in chosen:
            req_bytes  += to_bytes((1 << 31) | req,  31)
            resp_bytes += to_bytes((1 << 31) | resp, 32)
        dut.ib_ctrl.append(AXI4StreamTransaction(data=req_bytes))
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
        (1 << 31) | ControlRaw(command=ControlCommand.INTERVAL, payload=interval).pack(), 32
    )))

    # Read back the status to check an interval has been set
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | ControlRaw(command=ControlCommand.STATUS).pack(), 32
    )))
    dut.exp_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | ControlStatus(
            active      =0, # Inactive
            idle_low    =1, # Idle has been observed low
            first_tick  =1, # Fresh from reset
            interval_set=1  # An interval has been set
        ).pack(), 128
    )))

    # Wait for response
    while dut.exp_ctrl: await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)

    # Trigger a soft reset
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | ControlRaw(command=ControlCommand.RESET, payload=1).pack(), 32
    )))

    dut.info("Waiting for internal reset to rise")
    while dut.dut.u_dut.u_nexus.rst_internal == 0: await RisingEdge(dut.clk)
    dut.info("Waiting for internal reset to fall")
    while dut.dut.u_dut.u_nexus.rst_internal == 1: await RisingEdge(dut.clk)

    # Read back the status to check an interval has been cleared
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | ControlRaw(command=ControlCommand.STATUS).pack(), 32
    )))
    dut.exp_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | ControlStatus(
            active      =0, # Inactive
            idle_low    =1, # Idle has been observed low
            first_tick  =1, # Fresh from reset
            interval_set=0  # No interval has been set
        ).pack(), 128
    )))
