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

from itertools import product
from random import choice, randint, random

from cocotb.triggers import RisingEdge
from cocotb_bus.scoreboard import Scoreboard

from nxconstants import (ControlReqType, ControlRequest, NodeID, NodeParameter,
                         NODE_PARAM_WIDTH)

from drivers.basic.unstrobed import UnstrobedMonitor
from drivers.stream.common import StreamTransaction
from node.load import load_parameter

from ..testbench import testcase

@testcase()
async def parameters(dut):
    """ Update parameters using messages """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Read back mesh parameters
    num_rows = int(dut.ROWS)
    num_cols = int(dut.COLUMNS)

    # Create a proxy for loading into the mesh
    class InboundProxy:
        def append(self, tran):
            req                 = ControlRequest()
            req.to_mesh.command = ControlReqType.TO_MESH
            req.to_mesh.message = tran.data
            dut.ctrl_in.append(StreamTransaction(req.pack()))
        async def idle(self):
            await dut.ctrl_in.idle()
    proxy = InboundProxy()

    # Test nodes in a random order
    for row, col in sorted(
        product(range(num_rows), range(num_cols)), key=lambda _: random()
    ):
        node = dut.u_dut.u_mesh.gen_rows[row].gen_columns[col].u_node

        # Create monitors to track parameter updates
        um_num_instr = UnstrobedMonitor(
            dut, node.i_clk, node.i_rst, node.u_decoder.o_num_instr, "um_num_instr"
        )
        um_loopback = UnstrobedMonitor(
            dut, node.i_clk, node.i_rst, node.u_decoder.o_loopback_mask, "um_loopback"
        )

        # Scoreboard
        exp_num_instr = []
        exp_loopback  = []
        prm_sb        = Scoreboard(dut, fail_immediately=True)
        prm_sb.add_interface(um_num_instr, exp_num_instr)
        prm_sb.add_interface(um_loopback,  exp_loopback )

        # Send multiple update messages
        last_num_instr = 0
        last_loopback  = 0
        param_mask     = (1 << NODE_PARAM_WIDTH) - 1
        for _ in range(100):
            # Generate and queue message
            msg = load_parameter(
                inbound  =proxy,
                node_id  =NodeID(row=row, column=col),
                parameter=choice(list(NodeParameter)),
                value    =randint(0, (1 << NODE_PARAM_WIDTH) - 1),
            )
            # Track updates
            if msg.param == NodeParameter.INSTRUCTIONS and msg.value != last_num_instr:
                exp_num_instr.append(msg.value)
                last_num_instr = msg.value
            elif msg.param == NodeParameter.LOOPBACK and msg.value != (last_loopback & param_mask):
                last_loopback  &= param_mask
                last_loopback <<= NODE_PARAM_WIDTH
                last_loopback  |= msg.value & param_mask
                exp_loopback.append(last_loopback)

        # Wait for queues to drain
        while exp_num_instr: await RisingEdge(dut.clk)
        while exp_loopback : await RisingEdge(dut.clk)
