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

from random import choice, randint

from cocotb.triggers import RisingEdge
from cocotb_bus.scoreboard import Scoreboard

from nxconstants import (NodeCommand, NodeControl, NodeID, NodeParameter,
                         MAX_ROW_COUNT, MAX_COLUMN_COUNT, NODE_PARAM_WIDTH)
from drivers.basic.unstrobed import UnstrobedMonitor

from ..testbench import testcase

@testcase()
async def parameters(dut):
    """ Update parameters using messages """
    dut.info("Resetting the DUT")
    await dut.reset()

    # Create monitors to track parameter updates
    um_num_instr = UnstrobedMonitor(
        dut, dut.clk, dut.rst, dut.dut.u_dut.u_decoder.o_num_instr, "um_num_instr"
    )
    um_num_output = UnstrobedMonitor(
        dut, dut.clk, dut.rst, dut.dut.u_dut.u_decoder.o_num_output, "um_num_output"
    )

    # Scoreboard
    exp_num_instr  = []
    exp_num_output = []
    prm_sb         = Scoreboard(dut, fail_immediately=True)
    prm_sb.add_interface(um_num_instr,  exp_num_instr )
    prm_sb.add_interface(um_num_output, exp_num_output)

    # Decide on a row and column
    node_id = NodeID(
        row   =randint(0, MAX_ROW_COUNT-1   ),
        column=randint(0, MAX_COLUMN_COUNT-1),
    )
    dut.node_id <= node_id.pack()

    # Select an inbound pipe
    inbound = choice(dut.inbound)

    # Send multiple update messages
    last_num_instr  = 0
    last_num_output = 0
    for _ in range(1000):
        # Generate and queue message
        msg = NodeControl()
        msg.header.row     = node_id.row
        msg.header.column  = node_id.column
        msg.header.command = NodeCommand.CONTROL
        msg.param          = choice(list(NodeParameter))
        msg.value          = randint(0, (1 << NODE_PARAM_WIDTH) - 1)
        inbound.append((msg.pack(), 0))
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
