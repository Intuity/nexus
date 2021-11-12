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

from nxconstants import NodeID, NodeParameter, NODE_PARAM_WIDTH
from drivers.basic.unstrobed import UnstrobedMonitor
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

    # Select random nodes to test
    coords = sorted(product(range(num_rows), range(num_cols)), key=lambda _: random())[:4]
    for row, col in coords:
        node = dut.u_dut.u_mesh.gen_rows[row].gen_columns[col].u_node

        # Create monitors to track parameter updates
        um_num_instr = UnstrobedMonitor(
            dut, node.i_clk, node.i_rst, node.u_decoder.o_num_instr, "um_num_instr"
        )
        um_num_output = UnstrobedMonitor(
            dut, node.i_clk, node.i_rst, node.u_decoder.o_num_output, "um_num_output"
        )

        # Scoreboard
        exp_num_instr  = []
        exp_num_output = []
        prm_sb         = Scoreboard(dut, fail_immediately=True)
        prm_sb.add_interface(um_num_instr,  exp_num_instr )
        prm_sb.add_interface(um_num_output, exp_num_output)

        # Send multiple update messages
        last_num_instr  = 0
        last_num_output = 0
        for _ in range(1000):
            # Generate and queue message
            msg = load_parameter(
                inbound  =dut.mesh_inbound,
                node_id  =NodeID(row=row, column=col),
                parameter=choice(list(NodeParameter)),
                value    =randint(0, (1 << NODE_PARAM_WIDTH) - 1),
            )
            # Track updates
            if msg.param == NodeParameter.INSTRUCTIONS and msg.value != last_num_instr:
                exp_num_instr.append(msg.value)
                last_num_instr = msg.value
            elif msg.param == NodeParameter.OUTPUTS and msg.value != last_num_output:
                exp_num_output.append(msg.value)
                last_num_output = msg.value

        # Wait for queues to drain
        while exp_num_instr : await RisingEdge(dut.clk)
        while exp_num_output: await RisingEdge(dut.clk)
