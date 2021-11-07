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

from cocotb.triggers import ClockCycles, RisingEdge

from node.inputs import update_inputs
from node.instrs import gen_instructions
from node.load import load_data, load_loopback, load_parameter
from node.outputs import gen_output_mappings
from nxconstants import (NodeCommand, NodeID, NodeParameter, NodeSignal,
                         MAX_ROW_COUNT, MAX_COLUMN_COUNT)

from ..testbench import testcase

@testcase()
async def execute(dut):
    """ Execute a random instruction stream with random output mappings """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Pickup node parameters
    num_inputs    = int(dut.INPUTS)
    num_outputs   = int(dut.OUTPUTS)
    num_registers = int(dut.REGISTERS)
    num_entries   = (1 << int(dut.RAM_ADDR_W))
    ram_data_w    = int(dut.RAM_DATA_W)

    # Decide on a row and column
    node_id = NodeID(
        row   =randint(0, MAX_ROW_COUNT-1   ),
        column=randint(0, MAX_COLUMN_COUNT-1),
    )
    dut.node_id <= node_id.pack()

    # Generate an instruction stream
    instrs = gen_instructions(
        int(0.75 * num_entries), num_inputs, num_outputs, num_registers
    )

    # Generate output mappings
    lookup, mappings = gen_output_mappings(
        num_outputs, num_inputs, base_off=len(instrs), max_tgts=4
    )

    # Choose an interface
    inbound = choice(dut.inbound)

    # Load the different streams
    dut.info(f"Loading stream of {len(instrs)} instruction")
    load_data(inbound, node_id, ram_data_w, instrs)
    dut.info("Loading output lookup table")
    load_data(inbound, node_id, ram_data_w, lookup)
    dut.info("Loading output mappings")
    load_data(inbound, node_id, ram_data_w, sum(mappings, []))

    # Setup the number of instructions and outputs
    load_parameter(inbound, node_id, NodeParameter.INSTRUCTIONS, len(instrs))
    load_parameter(inbound, node_id, NodeParameter.OUTPUTS,      len(lookup))

    # Setup the loopback mask
    lb_mask = randint(0, (1 << num_inputs) - 1)
    dut.info(f"Setting loopback mask to 0x{lb_mask:08X}")
    load_loopback(inbound, node_id, num_inputs, lb_mask)

    # Wait for the inbound queue to go idle
    await inbound.idle()
    await ClockCycles(dut.clk, 10)

    # Disable scoreboarding of outbound messages
    for outbound in dut.outbound: outbound._callbacks = []

    # Run multiple cycles
    inputs  = [False] * num_inputs
    outputs = {}
    is_seq  = [choice((True, False)) for _ in range(num_inputs)]
    for cycle in range(1000):
        # Seed the inputs to a random state
        old_in = inputs[:]
        inputs = [choice((True, False)) for _ in range(num_inputs)]
        dut.info(
            f"Starting cycle {cycle} with inputs 0x"
            f"{sum((x << i) for i, x in enumerate(inputs)):08X}"
        )
        await update_inputs(
            choice(dut.inbound), node_id, old_in, inputs, is_seq, only_seq=True
        )
        # Wait for node to return to idle
        while dut.idle == 0: await RisingEdge(dut.clk)
        # Trigger the node
        dut.trigger <= 1
        await RisingEdge(dut.clk)
        dut.trigger <= 0
        await RisingEdge(dut.clk)
        # Wait for node to become busy
        while dut.idle == 1: await RisingEdge(dut.clk)
        # After a few cycles, update combinatorial inputs
        await ClockCycles(dut.clk, randint(10, 20))
        await update_inputs(
            choice(dut.inbound), node_id, old_in, inputs, is_seq, only_com=True
        )
        # Wait for node to return to idle
        while dut.idle == 0: await RisingEdge(dut.clk)
        # Parse all outbound messages to summarise the outputs
        all_msgs = []
        for outbound in dut.outbound:
            while outbound._recvQ: all_msgs.append(outbound._recvQ.pop())
        # Summarise
        for raw in sorted(all_msgs, key=lambda x: x.timestamp):
            msg = NodeSignal()
            msg.unpack(raw.data)
            assert msg.header.command == NodeCommand.SIGNAL, \
                f"Unexpected command type: {msg.header.command}"
            outputs[(msg.header.row, msg.header.column, msg.index)] = msg.state
