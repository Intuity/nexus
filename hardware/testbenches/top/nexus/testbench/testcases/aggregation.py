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

from collections import defaultdict
from random import choice, randint

from cocotb.triggers import RisingEdge

from drivers.stream.common import StreamTransaction
from nxconstants import (ControlReqType, ControlRespType, ControlRequest,
                         ControlResponse, NodeCommand, NodeSignal)

from ..testbench import testcase

@testcase()
async def aggregation(dut):
    """ Exercise SIGNAL message aggregation into an output vector """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Find the number of rows
    num_rows = int(dut.ROWS)
    num_cols = int(dut.COLUMNS)
    num_outs = int(dut.OUTPUTS)

    # Keep track of the output state
    state = defaultdict(lambda: 0)

    # Decide on a number of cycles to run for
    cycles = randint(10, 50)

    # Set the controller to active (will generate pulses)
    trig                  = ControlRequest()
    trig.trigger.command  = ControlReqType.TRIGGER
    trig.trigger.col_mask = (1 << num_cols) - 1
    trig.trigger.active   = 1
    trig.trigger.cycles   = cycles
    dut.ctrl_in.append(StreamTransaction(trig.trigger.pack()))

    # Run for a number of passes
    for idx_pass in range(cycles):
        dut.info(f"Starting pass {idx_pass}")

        # Stream in a bunch of signal messages
        for _ in range(num_cols * num_outs):
            # Generate a random update
            msg                = NodeSignal()
            msg.header.row     = num_rows
            msg.header.column  = randint(0, num_cols-1)
            msg.header.command = NodeCommand.SIGNAL
            msg.is_seq         = choice((0, 1))
            msg.index          = randint(0, num_outs-1)
            msg.state          = choice((0, 1))

            # Keep track of the state
            state[(msg.header.column * num_outs) + msg.index] = msg.state

            # Queue up the message
            req                 = ControlRequest()
            req.to_mesh.command = ControlReqType.TO_MESH
            req.to_mesh.message = msg.pack()
            dut.ctrl_in.append(StreamTransaction(req.to_mesh.pack()))

        # Queue up the output response
        resp = ControlResponse()
        resp.outputs.format = ControlRespType.OUTPUTS
        resp.outputs.stamp  = idx_pass
        resp.outputs.index   = 0
        resp.outputs.section = sum([(v << k) for k, v in state.items()])
        dut.expected.append(StreamTransaction(resp.outputs.pack()))

        # Wait for the driver, mesh, and aggregators to go idle
        dut.info(f"Waiting for driver to drain {len(dut.ctrl_in._sendQ)} messages")
        await dut.ctrl_in.idle()
        dut.info("Waiting for mesh to return to idle")
        while dut.status.idle == 0: await RisingEdge(dut.clk)

        # Check outputs
        dut.info("Checking outputs")
        for idx_out in range(num_cols * num_outs):
            got = int(dut.u_dut.u_mesh.o_outputs[idx_out])
            exp = state[idx_out]
            assert got == exp, f"Output {idx_out} - got {got} != expected {exp}"
