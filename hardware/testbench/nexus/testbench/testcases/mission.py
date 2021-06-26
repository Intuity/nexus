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

import io
from random import choice, randint

from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge

from nx_message import build_load_instr, build_map_input, build_map_output
from nxmodel.manager import Manager
from nxmodel.message import ConfigureInput, ConfigureOutput, LoadInstruction

from ..testbench import testcase

@testcase()
async def mission_mode(dut):
    """ Load up and run a real design """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Determine parameters
    num_rows = int(dut.dut.dut.ROWS)
    num_cols = int(dut.dut.dut.COLUMNS)
    dut.info(f"Mesh size - rows {num_rows}, columns {num_cols}")

    # Load a design using the nxmodel's Manager class
    mngr = Manager(None, None, None, False)
    mngr.load(dut.base_dir / "data" / "design.json")
    dsgn_rows = mngr.config[Manager.CONFIG_ROWS]
    dsgn_cols = mngr.config[Manager.CONFIG_COLUMNS]
    assert dsgn_rows == num_rows, \
        f"Design requires {dsgn_rows} rows, mesh has {num_rows} rows"
    assert dsgn_cols == num_cols, \
        f"Design requires {dsgn_cols} columns, mesh has {num_cols} columns"

    # Push all of the queued messages into the design
    loaded = [[[] for _y in range(num_cols)] for _x in range(num_rows)]
    for msg in mngr.queue:
        common = (1 if msg.broadcast else 0, msg.tgt_row, msg.tgt_col, msg.decay)
        # Attempt to translate the message
        if isinstance(msg, ConfigureInput):
            dut.inbound.append(build_map_input(
                *common, msg.tgt_pos, 1 if msg.state else 0, msg.src_row,
                msg.src_col, msg.src_pos,
            ))
        elif isinstance(msg, ConfigureOutput):
            if msg.msg_as_bc:
                dut.inbound.append(build_map_output(
                    *common, msg.out_pos, 0, 1, (msg.bc_decay >> 4) & 0xF,
                    (msg.bc_decay >> 0) & 0xF,
                ))
            else:
                dut.inbound.append(build_map_output(
                    *common, msg.out_pos, 0, 0, msg.msg_a_row, msg.msg_a_col
                ))
                dut.inbound.append(build_map_output(
                    *common, msg.out_pos, 1, 0, msg.msg_b_row, msg.msg_b_col
                ))
        elif isinstance(msg, LoadInstruction):
            dut.inbound.append(build_load_instr(*common, 0, msg.instr.raw))
            if not msg.broadcast:
                loaded[msg.tgt_row][msg.tgt_col].append(msg.instr.raw)
        else:
            raise Exception(f"Unexpected message {msg}")

    # Wait for the inbound driver to drain
    dut.info(f"Waiting for {len(dut.inbound._sendQ)} messages to drain")
    while dut.inbound._sendQ: await RisingEdge(dut.clk)
    while dut.inbound.intf.valid == 1: await RisingEdge(dut.clk)

    # Plot the mesh state
    dut.plot_mesh_state("loading.png")

    # Wait for the idle flag to go high
    if dut.dut.dut.mesh.idle_o == 0: await RisingEdge(dut.dut.dut.mesh.idle_o)

    # Wait for some extra time
    await ClockCycles(dut.clk, 10)

    # Start monitoring the mesh
    dut.info("Starting node monitors")
    dut.start_node_monitors()

    # Check the instruction counters for every core
    for row in range(num_rows):
        for col in range(num_cols):
            node   = dut.nodes[row][col].entity
            core_0 = int(node.instr_store.core_0_populated_o)
            core_1 = int(node.instr_store.core_1_populated_o)
            assert core_0 == len(loaded[row][col]), \
                f"{row}, {col}: Expected {len(loaded[row][col])}, got {core_0}"
            assert core_1 == 0, \
                f"{row}, {col}: Expected 0, got {core_1}"
            # Check the loaded instructions
            dut.info(f"Checking {len(loaded[row][col])} instructions for {row}, {col}")
            for idx, instr in enumerate(loaded[row][col]):
                got = int(node.instr_store.ram.memory[idx])
                assert instr == got, f"Instruction {idx} - {hex(instr)=}, {hex(got)=}"

    # Build a map for linked inputs and outputs
    linked = {}
    seq_in = {}
    bc_out = {}
    slots  = {}
    for msg in mngr.queue:
        # Filter input messages to build up a picture of the links
        if isinstance(msg, ConfigureInput):
            # Create mapping
            src_key = msg.src_row, msg.src_col, msg.src_pos
            tgt_key = msg.tgt_row, msg.tgt_col, msg.tgt_pos
            if src_key not in linked: linked[src_key] = []
            linked[src_key].append(tgt_key)
            # Mark if this input is sequential
            seq_in[tgt_key] = msg.state
        # Filter output messages to detect broadcast
        elif isinstance(msg, ConfigureOutput):
            src_key = msg.tgt_row, msg.tgt_col, msg.out_pos
            bc_out[src_key] = msg.msg_as_bc
            if not msg.msg_as_bc:
                slots[src_key] = (
                    (msg.msg_a_row, msg.msg_a_col),
                    (msg.msg_b_row, msg.msg_b_col),
                )

    # Print out how many nodes are blocked
    for cycle in range(10):
        # Trigger a single cycle
        dut.info("Triggering a single cycle")
        await RisingEdge(dut.clk)
        dut.active_i <= 1
        await RisingEdge(dut.clk)
        dut.active_i <= 0
        await RisingEdge(dut.clk)

        # Wait for activity
        dut.info("Waiting for idle to fall")
        if dut.dut.dut.mesh.idle_o == 1: await FallingEdge(dut.dut.dut.mesh.idle_o)

        # Wait for idle
        dut.info("Waiting for idle to rise")
        await RisingEdge(dut.dut.dut.mesh.idle_o)

        # Little delay
        await ClockCycles(dut.clk, 100)

        # Print out the input state for every node
        for row, row_entries in enumerate(dut.nodes):
            for col, node in enumerate(row_entries):
                ctrl = node.entity.control
                i_curr = int(ctrl.input_curr_q)
                i_next = int(ctrl.input_next_q)
                o_curr = int(ctrl.output_last_q)
                dut.info(
                    f"[{cycle:04d}] {row:2d}, {col:2d} - IC: {i_curr:08b}, "
                    f"IN: {i_next:08b}, OC: {o_curr:08b} - Δ: {i_curr != i_next}"
                )

        # Check for I/O consistency
        io_error = 0
        io_match = 0
        for (src_row, src_col, src_pos), entries in linked.items():
            src_node = dut.nodes[src_row][src_col]
            src_out  = int(src_node.entity.control.output_last_q[src_pos])
            for tgt_row, tgt_col, tgt_pos in entries:
                tgt_node = dut.nodes[tgt_row][tgt_col]
                tgt_in   = int(tgt_node.entity.control.input_next_q[tgt_pos])
                if src_out != tgt_in:
                    is_bc_out = bc_out[src_row, src_col, src_pos]
                    is_seq_in = seq_in[tgt_row, tgt_col, tgt_pos]
                    slots_out = slots.get((src_row, src_col, src_pos), None)
                    dut.error(
                        f"I/O Mismatch: {src_row}, {src_col} O[{src_pos}] -> "
                        f"{tgt_row}, {tgt_col} I[{tgt_pos}]: {src_out=}, "
                        f"{tgt_in=} - BC: {is_bc_out}, Seq: {is_seq_in}, "
                        f"Slots: {slots_out}"
                    )
                    io_error += 1
                else:
                    io_match += 1
        assert io_error == 0, \
            f"{io_error} I/O inconsistencies detected, while {io_match} matched"
