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

from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge
import simpy

from nx_constants import Command
from nx_control import build_set_active
from nx_message import build_load_instr, build_map_output
from nxmodel.base import Base
from nxmodel.capture import Capture
from nxmodel.manager import Manager
from nxmodel.mesh import Mesh
from nxmodel.message import ConfigureOutput, LoadInstruction
from nxmodel.node import Direction
from nxmodel.pipe import Pipe

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

    # Disable scoreboarding of output
    dut.mesh_outbound._callbacks = []

    # Setup an instance of nxmodel to match the design
    env = simpy.Environment()
    Base.setup_log(env, "INFO")
    mesh = Mesh(env, num_rows, num_cols, nd_prms={
        "inputs"   : int(dut.dut.dut.INPUTS),
        "outputs"  : int(dut.dut.dut.OUTPUTS),
        "registers": int(dut.dut.dut.REGISTERS),
    })

    # Create a manager and load the design
    mngr = Manager(env, mesh, 1000, False)
    mesh[0, 0].inbound[Direction.NORTH] = mngr.outbound
    out_lkp = mngr.load(dut.base_dir / "data" / "design.json")
    dsgn_rows = mngr.config[Manager.CONFIG_ROWS]
    dsgn_cols = mngr.config[Manager.CONFIG_COLUMNS]
    assert dsgn_rows == num_rows, \
        f"Design requires {dsgn_rows} rows, mesh has {num_rows} rows"
    assert dsgn_cols == num_cols, \
        f"Design requires {dsgn_cols} columns, mesh has {num_cols} columns"

    # Create a capture node
    cap = Capture(env, mesh, num_cols, out_lkp)
    for col, node in enumerate(mesh.nodes[num_rows-1]):
        cap.inbound[col] = node.outbound[Direction.SOUTH] = Pipe(env, 1, 1)
    mngr.add_observer(cap.tick)

    # Push all of the queued messages into the design
    linked, seq_in = {}, {}
    for msg in mngr.queue:
        if isinstance(msg, ConfigureOutput):
            dut.mesh_inbound.append(build_map_output(
                msg.row, msg.col, msg.src_idx,
                msg.tgt_row, msg.tgt_col, msg.tgt_idx, msg.tgt_seq
            ))
            # Setup source if not already tracked
            src_key = msg.row, msg.col, msg.src_idx
            if src_key not in linked: linked[src_key] = []
            # Add a target entry
            tgt_key = msg.tgt_row, msg.tgt_col, msg.tgt_idx
            linked[src_key].append(tgt_key)
            # Track sequential inputs
            assert tgt_key not in seq_in, f"Clash for target: {tgt_key}"
            seq_in[tgt_key] = msg.tgt_seq
        elif isinstance(msg, LoadInstruction):
            dut.mesh_inbound.append(build_load_instr(msg.row, msg.col, msg.instr.raw))
        else:
            raise Exception(f"Unexpected message {msg}")

    # Wait for the inbound driver to drain
    dut.info(f"Waiting for {len(dut.mesh_inbound._sendQ)} messages to drain")
    while dut.mesh_inbound._sendQ: await RisingEdge(dut.clk)
    while dut.mesh_inbound.intf.valid == 1: await RisingEdge(dut.clk)

    # Wait for the idle flag to go high
    if dut.dut.dut.mesh.idle_o == 0: await RisingEdge(dut.dut.dut.mesh.idle_o)

    # Wait for some extra time
    await ClockCycles(dut.clk, 10)

    # Run until idle to flush model setup
    dut.info("Running model until first tick")
    env.run(until=mngr.on_tick)
    dut.info("Model reached until first tick")

    # Start monitoring the mesh
    dut.info("Starting node monitors")
    dut.start_node_monitors()

    # Check the instruction counters for every core
    for row in range(num_rows):
        for col in range(num_cols):
            rtl_node = dut.nodes[row][col].entity
            mdl_node = mesh.nodes[row][col]
            i_count  = int(rtl_node.store.instr_count_o)
            assert i_count == len(mdl_node.instrs), \
                f"{row}, {col}: Expected {len(mdl_node.instrs)}, got {i_count}"
            # Check the loaded instructions
            dut.info(f"Checking {len(mdl_node.instrs)} instructions for {row}, {col}")
            for idx, instr in enumerate(mdl_node.instrs):
                got = int(rtl_node.store.ram.memory[idx])
                assert instr.raw == got, \
                    f"Instruction {idx} - {hex(instr.raw)=}, {hex(got)=}"

    # Raise active and let nexus tick
    dut.info("Enabling nexus")
    dut.ctrl_inbound.append(build_set_active(1))

    # Print out how many nodes are blocked
    rtl_outputs = {}
    for cycle in range(256):
        # Run the model for one tick
        dut.info("Running model until tick")
        env.run(until=mngr.on_tick)
        dut.info("Model reached next tick")

        # Wait for activity
        dut.info("Waiting for idle to fall")
        if dut.dut.dut.mesh.idle_o == 1: await FallingEdge(dut.dut.dut.mesh.idle_o)

        # Wait for idle (ensuring it is synchronous)
        dut.info("Waiting for idle to rise")
        while True:
            await RisingEdge(dut.dut.dut.mesh.idle_o)
            await RisingEdge(dut.clk)
            if dut.dut.dut.mesh.idle_o == 1: break

        # Print out the input state for every node
        for row, row_entries in enumerate(dut.nodes):
            for col, node in enumerate(row_entries):
                ctrl = node.entity.control
                i_curr = int(ctrl.input_curr_q)
                i_next = int(ctrl.input_next_q)
                o_curr = int(ctrl.detect_last_q)
                dut.info(
                    f"[{cycle:04d}] {row:2d}, {col:2d} - IC: {i_curr:08b}, "
                    f"IN: {i_next:08b}, OC: {o_curr:08b} - Δ: {i_curr != i_next}"
                )

        # Check for I/O consistency
        io_error = 0
        io_match = 0
        for (src_row, src_col, src_pos), entries in linked.items():
            src_node = dut.nodes[src_row][src_col]
            src_out  = int(src_node.entity.control.detect_last_q[src_pos])
            for tgt_row, tgt_col, tgt_pos in entries:
                # Skip out-of-range rows (temporarily used for top-level outputs)
                if tgt_row >= num_rows: continue
                # Lookup the target node
                tgt_node = dut.nodes[tgt_row][tgt_col]
                tgt_in   = int(tgt_node.entity.control.input_next_q[tgt_pos])
                if src_out != tgt_in:
                    is_seq_in = seq_in[tgt_row, tgt_col, tgt_pos]
                    dut.error(
                        f"I/O Mismatch: {src_row}, {src_col} O[{src_pos}] -> "
                        f"{tgt_row}, {tgt_col} I[{tgt_pos}]: {src_out=}, "
                        f"{tgt_in=} - Seq: {is_seq_in}"
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
                rtl_i_curr = int(ctrl.input_curr_q)
                rtl_i_next = int(ctrl.input_next_q)
                rtl_o_curr = int(ctrl.detect_last_q)
                # Get the model state
                mdl_node   = mesh.nodes[row][col]
                mdl_i_curr = sum([(y << x) for x, y in enumerate(mdl_node.input_state)])
                mdl_i_next = sum([(y << x) for x, y in enumerate(mdl_node.next_input_state)])
                mdl_o_curr = sum([(y << x) for x, y in enumerate(mdl_node.output_state)])
                # Compare
                if rtl_i_curr != mdl_i_curr:
                    dut.error(f"{row}, {col} - {rtl_i_curr=:08b}, {mdl_i_curr=:08b}")
                    mm_i_curr += 1
                if rtl_i_next != mdl_i_next:
                    dut.error(f"{row}, {col} - {rtl_i_next=:08b}, {mdl_i_next=:08b}")
                    mm_i_next += 1
                if rtl_o_curr != mdl_o_curr:
                    dut.error(f"{row}, {col} - {rtl_o_curr=:08b}, {mdl_o_curr=:08b}")
                    mm_o_curr += 1
        assert mm_i_curr == 0, f"Detected {mm_i_curr} current input mismatches"
        assert mm_i_next == 0, f"Detected {mm_i_next} next input mismatches"
        assert mm_o_curr == 0, f"Detected {mm_o_curr} current output mismatches"

        # Build up a final output state for RTL
        while dut.mesh_outbound._recvQ:
            msg, _  = dut.mesh_outbound._recvQ.pop()
            command = (msg >> 21) & 0x3
            if command == int(Command.SIG_STATE):
                rtl_row = (msg >> 17) & 0xF
                rtl_col = (msg >> 13) & 0xF
                rtl_idx = (msg >> 10) & 0x7
                rtl_val = (msg >>  9) & 0x1
                rtl_outputs[rtl_row, rtl_col, rtl_idx] = rtl_val

        # Capture and check against the model's output state
        cap.snapshot()
        for key, mdl_val in cap.snapshots[-1][1].items():
            assert key in rtl_outputs, f"Missing output {key=}"
            assert mdl_val == rtl_outputs[key], \
                f"Output {key} differs {mdl_val=}, {rtl_val=}"
