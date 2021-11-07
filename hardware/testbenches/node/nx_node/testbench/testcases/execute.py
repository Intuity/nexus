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

from nxmodel import direction_t, NXMessagePipe, NXNode, pack_node_raw, node_raw_t

from node.inputs import update_inputs
from node.instrs import gen_instructions, print_instructions
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

    # Create an instance of the node model
    model    = NXNode(node_id.row, node_id.column)
    mdl_ins  = [model.get_pipe(direction_t(i)) for i in range(4)]
    mdl_outs = [NXMessagePipe() for _ in range(4)]
    for idx, pipe in enumerate(mdl_outs):
        model.attach(direction_t(idx), pipe)

    # Generate an instruction stream
    instrs = gen_instructions(
        int(0.75 * num_entries), num_inputs, num_outputs, num_registers
    )

    # Generate output mappings
    lookup, mappings = gen_output_mappings(
        num_outputs, num_inputs, base_off=len(instrs), max_tgts=4
    )

    # Choose an interface
    rtl_in, mdl_in = choice(list(zip(dut.inbound, mdl_ins)))

    # Load the different streams
    dut.info(f"Loading stream of {len(instrs)} instructions")
    load_data(rtl_in, node_id, ram_data_w, instrs, model=mdl_in)
    dut.info("Loading output lookup table")
    load_data(rtl_in, node_id, ram_data_w, lookup, model=mdl_in)
    dut.info("Loading output mappings")
    load_data(rtl_in, node_id, ram_data_w, sum(mappings, []), model=mdl_in)

    # Setup the number of instructions and outputs
    load_parameter(
        rtl_in, node_id, NodeParameter.INSTRUCTIONS, len(instrs), model=mdl_in
    )
    load_parameter(
        rtl_in, node_id, NodeParameter.OUTPUTS, len(lookup), model=mdl_in
    )

    # Setup the loopback mask
    loopback = [choice((0, 1)) for _ in range(num_inputs)]
    lb_mask  = sum((x << i) for i, x in enumerate(loopback))
    dut.info(f"Setting loopback mask to 0x{lb_mask:08X}")
    load_loopback(rtl_in, node_id, num_inputs, lb_mask, model=mdl_in)

    # Wait for the inbound queue to go idle
    dut.info("Waiting for RTL to return to idle")
    await rtl_in.idle()
    await ClockCycles(dut.clk, 10)

    # Tick the model until it goes idle
    dut.info("Waiting for model to return to idle")
    while True:
        model.step(False)
        if model.is_idle(): break

    # Disable scoreboarding of outbound messages
    for outbound in dut.outbound: outbound._callbacks = []

    # Run multiple cycles
    inputs      = [False] * num_inputs
    rtl_outputs = {}
    mdl_outputs = {}
    is_seq      = [choice((True, False)) for _ in range(num_inputs)]
    for cycle in range(1000):
        # Seed the inputs to a random state
        old_in = inputs[:]
        inputs = [((not lb) and choice((True, False))) for lb in loopback]
        dut.info(
            f"Starting cycle {cycle} with inputs 0x"
            f"{sum((x << i) for i, x in enumerate(inputs)):08X}"
        )
        await update_inputs(
            choice(dut.inbound), node_id, old_in, inputs, is_seq, only_seq=True,
            model=choice(mdl_ins),
        )
        await RisingEdge(dut.clk)
        model.step(False)
        # Wait for node to return to idle
        while dut.idle == 0: await RisingEdge(dut.clk)
        # Trigger the node
        dut.trigger <= 1
        await RisingEdge(dut.clk)
        dut.trigger <= 0
        await RisingEdge(dut.clk)
        # Trigger model
        model.step(True)
        # Wait for node to become busy
        while dut.idle == 1: await RisingEdge(dut.clk)
        # After a few cycles, update combinatorial inputs
        await ClockCycles(dut.clk, randint(10, 20))
        await update_inputs(
            choice(dut.inbound), node_id, old_in, inputs, is_seq, only_com=True,
            model=choice(mdl_ins),
        )
        # Wait for node to return to idle
        while dut.idle == 0: await RisingEdge(dut.clk)
        # Run model until idle
        while True:
            model.step(False)
            if model.is_idle(): break
        # Check input and output state
        input_err, output_err = 0, 0
        for index, (seq, lb) in enumerate(zip(is_seq, loopback)):
            exp    = (1 if inputs[index] else 0)
            rtl    = int(dut.dut.u_dut.u_core.i_inputs[index])
            mdl    = (1 if model.get_current_inputs().get(index, 0) else 0)
            prefix = f"I[{index:2d}] {'S' if seq else ''}{'L' if lb else ' '}"
            # For non-loopback ports, check for RTL match against expected
            if not lb: assert rtl == exp, f"{prefix} - RTL: {rtl} != EXP: {exp}"
            if rtl != mdl:
                dut.error(f"{prefix} - RTL: {rtl} != MDL: {mdl}")
                input_err += 1
        for index in range(num_outputs):
            rtl = int(dut.dut.u_dut.u_core.o_outputs[index])
            mdl = (1 if model.get_current_outputs().get(index, 0) else 0)
            if rtl != mdl:
                dut.error(f"O[{index}] - RTL: {rtl} != MDL: {mdl}")
                output_err += 1
        assert input_err == 0, f"{input_err} input mismatches detected"
        assert output_err == 0, f"{output_err} output mismatches detected"
        # Parse all outbound messages to summarise the outputs
        rtl_msgs = []
        for outbound in dut.outbound:
            while outbound._recvQ: rtl_msgs.append(outbound._recvQ.pop())
        # Summarise
        for raw in sorted(rtl_msgs, key=lambda x: x.timestamp):
            msg = NodeSignal()
            msg.unpack(raw.data)
            assert msg.header.command == NodeCommand.SIGNAL, \
                f"Unexpected command type: {msg.header.command}"
            rtl_outputs[(msg.header.row, msg.header.column, msg.index)] = msg.state
        # Dequeue and summarise all model messages
        for outbound in mdl_outs:
            while not outbound.is_idle():
                raw = node_raw_t()
                outbound.dequeue(raw)
                msg = NodeSignal()
                msg.unpack(pack_node_raw(raw))
                mdl_outputs[(msg.header.row, msg.header.column, msg.index)] = msg.state
        # Check RTL against the model
        rtl_keys = [x for x in rtl_outputs.keys()]
        mdl_keys = [x for x in mdl_outputs.keys()]
        for row, column, index in set(rtl_keys + mdl_keys):
            rtl_val = rtl_outputs.get((row, column, index), 0)
            mdl_val = mdl_outputs.get((row, column, index), 0)
            assert rtl_val == mdl_val, \
                f"O[{row}, {column}, {index}] - RTL {rtl_val} != MDL {mdl_val}"
