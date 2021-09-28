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

from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge

from nxconstants import ControlCommand, ControlSetActive, NodeCommand

from nxmodel import Nexus, NXLoader
from nxloader import NXLoader as NXPyLoader

from drivers.axi4stream.common import AXI4StreamTransaction

from ..testbench import testcase

def to_bytes(data, bits):
    return bytearray([((data >> (x * 8)) & 0xFF) for x in range(int(ceil(bits / 8)))])

@testcase()
async def mission_mode(dut):
    """ Load up and run a real design """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Determine parameters
    num_rows = int(dut.dut.dut.core.ROWS)
    num_cols = int(dut.dut.dut.core.COLUMNS)
    nd_ips   = int(dut.dut.dut.core.INPUTS)
    nd_ops   = int(dut.dut.dut.core.OUTPUTS)
    nd_regs  = int(dut.dut.dut.core.REGISTERS)
    dut.info(f"Mesh size - rows {num_rows}, columns {num_cols}")

    # Disable scoreboarding of output
    dut.ob_mesh._callbacks = []

    # Work out the full path
    full_path = dut.base_dir / "data" / "design.json"

    # Create an instance of NXModel
    model = Nexus(num_rows, num_cols)
    NXLoader(model, full_path.as_posix())

    # Load the design using the Python loader
    design = NXPyLoader().load(full_path)

    # Push all of the queued messages into the design
    linked, seq_in = {}, {}
    to_send        = bytearray()
    for row in zip(design.instructions, design.mappings):
        for instrs, mappings in zip(*row):
            for msg in instrs:
                to_send += to_bytes((1 << 31) | msg.pack(), 32)
            for msg in mappings:
                to_send += to_bytes((1 << 31) | msg.pack(), 32)
                # Setup source if not already tracked
                src_key = msg.header.row, msg.header.column, msg.source_index
                if src_key not in linked: linked[src_key] = []
                # Add a target entry
                tgt_key = msg.target_row, msg.target_column, msg.target_index
                linked[src_key].append(tgt_key)
                # Track sequential inputs
                assert tgt_key not in seq_in, f"Clash for target: {tgt_key}"
                seq_in[tgt_key] = msg.target_is_seq

    # Create a single AXI4-Stream transaction to send all configuratioj
    dut.ib_mesh.append(AXI4StreamTransaction(data=to_send))

    # Wait for all data to be sent
    dut.info("Waiting for AXI4-stream to send all data")
    await dut.ib_mesh.idle()

    # Wait for the idle flag to go high
    dut.info("Waiting for idle to rise")
    while True:
        await RisingEdge(dut.status_idle)
        await RisingEdge(dut.clk)
        if dut.status_idle == 1: break

    # Wait for some extra time
    await ClockCycles(dut.clk, 10)

    # Start monitoring the mesh
    dut.info("Starting node monitors")
    dut.start_node_monitors()

    # Check the instruction counters for every core
    for row in range(num_rows):
        for col in range(num_cols):
            rtl_node  = dut.nodes[row][col].entity
            mdl_node  = model.get_mesh().get_node(row, col)
            mdl_instr = mdl_node.get_instructions()
            i_count   = int(rtl_node.store.instr_count_o)
            assert i_count == len(mdl_instr), \
                f"{row}, {col}: Expected {len(mdl_instr)}, got {i_count}"
            # Check the loaded instructions
            dut.info(f"Checking {len(mdl_instr)} instructions for {row}, {col}")
            for idx, instr in enumerate(mdl_instr):
                got = int(rtl_node.store.ram.memory[idx])
                assert instr == got, f"Instruction {idx} - R: {hex(instr)}, G: {hex(got)}"

    # Raise active and let nexus tick
    dut.info("Enabling nexus")
    dut.ib_ctrl.append(AXI4StreamTransaction(data=to_bytes(
        (1 << 31) | ControlSetActive(command=ControlCommand.ACTIVE, active=1).pack(),
        32
    )))

    # Wait for all data to be sent
    dut.info("Waiting for AXI4-stream to send all data")
    await dut.ib_ctrl.idle()

    # Print out how many nodes are blocked
    rtl_outputs, mdl_outputs = {}, {}
    for cycle in range(256):
        # Run the model for one tick
        dut.info("Running model until tick")
        model.run(1)
        dut.info("Model reached next tick")

        # Wait for activity
        dut.info("Waiting for idle to fall")
        if dut.status_idle == 1:
            while True:
                await FallingEdge(dut.status_idle)
                await RisingEdge(dut.clk)
                if dut.status_idle == 0: break

        # Wait for idle (ensuring it is synchronous)
        dut.info("Waiting for idle to rise")
        while True:
            await RisingEdge(dut.status_idle)
            await RisingEdge(dut.clk)
            if dut.status_idle == 1: break

        # Print out the input state for every node
        for row, row_entries in enumerate(dut.nodes):
            for col, node in enumerate(row_entries):
                ctrl = node.entity.control
                i_curr = int(ctrl.ctrl_inputs.input_curr_q)
                i_next = int(ctrl.ctrl_inputs.input_next_q)
                o_curr = int(ctrl.ctrl_outputs.output_state_q)
                dut.info(
                    f"[{cycle:04d}] {row:2d}, {col:2d} - IC: {i_curr:0{nd_ips}b}, "
                    f"IN: {i_next:0{nd_ips}b}, OC: {o_curr:0{nd_ops}b} - Δ: "
                    f"{i_curr != i_next}"
                )

        # Check for I/O consistency
        io_error = 0
        io_match = 0
        for (src_row, src_col, src_pos), entries in linked.items():
            src_node = dut.nodes[src_row][src_col]
            src_out  = int(src_node.entity.control.ctrl_outputs.output_state_q[src_pos])
            for tgt_row, tgt_col, tgt_pos in entries:
                # Skip out-of-range rows (temporarily used for top-level outputs)
                if tgt_row >= num_rows: continue
                # Lookup the target node
                tgt_node = dut.nodes[tgt_row][tgt_col]
                tgt_in   = int(tgt_node.entity.control.ctrl_inputs.input_next_q[tgt_pos])
                if src_out != tgt_in:
                    is_seq_in = seq_in[tgt_row, tgt_col, tgt_pos]
                    dut.error(
                        f"I/O Mismatch: {src_row}, {src_col} O[{src_pos}] -> "
                        f"{tgt_row}, {tgt_col} I[{tgt_pos}]: SRC: {src_out}, "
                        f"TGT: {tgt_in} - Seq: {is_seq_in}"
                    )
                    io_error += 1
                else:
                    io_match += 1
        assert io_error == 0, \
            f"{io_error} I/O inconsistencies detected, while {io_match} matched"

        # Check state against the model
        mm_i_curr, mm_i_next, mm_o_curr = 0, 0, 0
        for row, row_entries in enumerate(dut.nodes):
            for col, rtl_node in enumerate(row_entries):
                # Get the RTL state
                ctrl       = rtl_node.entity.control
                rtl_i_curr = int(ctrl.ctrl_inputs.input_curr_q)
                rtl_i_next = int(ctrl.ctrl_inputs.input_next_q)
                rtl_o_curr = int(ctrl.ctrl_outputs.output_state_q)
                # Get the model state
                mdl_node   = model.get_mesh().get_node(row, col)
                mdl_i_curr = sum([(y << x) for x, y in mdl_node.get_current_inputs().items()])
                mdl_i_next = sum([(y << x) for x, y in mdl_node.get_next_inputs().items()])
                mdl_o_curr = sum([(y << x) for x, y in mdl_node.get_current_outputs().items()])
                # Compare
                if rtl_i_curr != mdl_i_curr:
                    dut.error(
                        f"{row}, {col} - RTL: {rtl_i_curr:0{nd_ips}b}, "
                        f"MDL: {mdl_i_curr:0{nd_ips}b}"
                    )
                    mm_i_curr += 1
                if rtl_i_next != mdl_i_next:
                    dut.error(
                        f"{row}, {col} - RTL: {rtl_i_next:0{nd_ips}b}, "
                        f"MDL: {mdl_i_next:0{nd_ips}b}"
                    )
                    mm_i_next += 1
                if rtl_o_curr != mdl_o_curr:
                    dut.error(
                        f"{row}, {col} - RTL: {rtl_o_curr:0{nd_ips}b}, "
                        f"MDL: {mdl_o_curr:0{nd_ips}b}"
                    )
                    mm_o_curr += 1
        assert mm_i_curr == 0, f"Detected {mm_i_curr} current input mismatches"
        assert mm_i_next == 0, f"Detected {mm_i_next} next input mismatches"
        assert mm_o_curr == 0, f"Detected {mm_o_curr} current output mismatches"

        # Wait for outbound AXI stream to go idle
        dut.info("Waiting for AXI stream to go idle")
        while dut.ob_mesh.intf.tvalid == 1: await RisingEdge(dut.clk)

        # Build up a final output state for RTL
        # NOTE: Receive queue must be reversed in order to accumulate correctly
        ob_trans = []
        while dut.ob_mesh._recvQ: ob_trans.append(dut.ob_mesh._recvQ.pop())
        for tran in ob_trans[::-1]:
            for msg, _ in tran.pack(4):
                # Skip unpopulated entries
                if ((msg >> 31) & 0x1) == 0: continue
                # Decode target row and column, and the command
                rtl_row = (msg >> 27) & 0xF
                rtl_col = (msg >> 23) & 0xF
                command = (msg >> 21) & 0x3
                # Capture signal state
                if command == int(NodeCommand.SIG_STATE):
                    rtl_idx = (msg >> 16) & 0x1F
                    rtl_val = (msg >> 14) & 0x01
                    rtl_outputs[rtl_row, rtl_col, rtl_idx] = rtl_val

        # Capture model outputs
        for key, mdl_val in model.pop_output().items():
            mdl_outputs[key] = mdl_val

        # Cross-check
        # NOTE: Missing RTL/model outputs could just be because of different
        #       settling behaviour - so just assume they are still at zero
        errors = 0
        for key in set(list(mdl_outputs.keys()) + list(rtl_outputs.keys())):
            rtl_val = rtl_outputs.get(key, 0)
            mdl_val = (1 if mdl_outputs.get(key, 0) else 0)
            if rtl_val != mdl_val:
                dut.error(f"Output {key} mismatch RTL: {rtl_val}, MDL: {mdl_val}")
                errors += 1
                continue
        assert errors == 0, f"{errors} errors were detected in outputs"
