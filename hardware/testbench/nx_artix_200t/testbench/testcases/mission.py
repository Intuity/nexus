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

from drivers.axi4stream.common import AXI4StreamTransaction
from nx_constants import Command
from nx_message import build_load_instr, build_map_input, build_map_output
from nxmodel.base import Base
from nxmodel.capture import Capture
from nxmodel.manager import Manager
from nxmodel.mesh import Mesh
from nxmodel.message import ConfigureInput, ConfigureOutput, LoadInstruction
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
    num_rows = int(dut.dut.dut.core.ROWS)
    num_cols = int(dut.dut.dut.core.COLUMNS)
    dut.info(f"Mesh size - rows {num_rows}, columns {num_cols}")

    # Disable scoreboarding of output
    dut.outbound._callbacks = []

    # Setup an instance of nxmodel to match the design
    env = simpy.Environment()
    Base.setup_log(env, "INFO")
    mesh = Mesh(env, num_rows, num_cols, nd_prms={
        "inputs"   : int(dut.dut.dut.core.INPUTS),
        "outputs"  : int(dut.dut.dut.core.OUTPUTS),
        "registers": int(dut.dut.dut.core.REGISTERS),
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
    linked, seq_in, bc_out, slots = {}, {}, {}, {}
    to_send = bytearray()
    for msg in mngr.queue:
        common = (1 if msg.broadcast else 0, msg.tgt_row, msg.tgt_col, msg.decay)
        # Message to send
        raw = []
        # Attempt to translate the message
        if isinstance(msg, ConfigureInput):
            raw.append(build_map_input(
                *common, msg.tgt_pos, 1 if msg.state else 0, msg.src_row,
                msg.src_col, msg.src_pos,
            ))
            # Use input mappings to build up a picture of the links
            src_key = msg.src_row, msg.src_col, msg.src_pos
            tgt_key = msg.tgt_row, msg.tgt_col, msg.tgt_pos
            if src_key not in linked: linked[src_key] = []
            linked[src_key].append(tgt_key)
            # Mark if this input is sequential
            seq_in[tgt_key] = msg.state
        elif isinstance(msg, ConfigureOutput):
            if msg.msg_as_bc:
                raw.append(build_map_output(
                    *common, msg.out_pos, 0, 1, (msg.bc_decay >> 4) & 0xF,
                    (msg.bc_decay >> 0) & 0xF,
                ))
            else:
                raw.append(build_map_output(
                    *common, msg.out_pos, 0, 0, msg.msg_a_row, msg.msg_a_col
                ))
                raw.append(build_map_output(
                    *common, msg.out_pos, 1, 0, msg.msg_b_row, msg.msg_b_col
                ))
            # Use output messages to mark broadcasts
            src_key = msg.tgt_row, msg.tgt_col, msg.out_pos
            bc_out[src_key] = msg.msg_as_bc
            if not msg.msg_as_bc:
                slots[src_key] = (
                    (msg.msg_a_row, msg.msg_a_col),
                    (msg.msg_b_row, msg.msg_b_col),
                )
        elif isinstance(msg, LoadInstruction):
            raw.append(build_load_instr(*common, 0, msg.instr.raw))
        else:
            raise Exception(f"Unexpected message {msg}")
        # Convert to bytes
        for entry in raw:
            to_send += bytearray([(entry >> (x * 8)) & 0xFF for x in range(4)])

    # Create a single AXI4-Stream transaction to send all configuratioj
    dut.inbound.append(AXI4StreamTransaction(data=to_send))

    # Wait for all data to be sent
    dut.info("Waiting for AXI4-stream to send all data")
    await dut.inbound.idle()

    # Wait for the idle flag to go high
    if dut.dut.dut.core.mesh.idle_o == 0: await RisingEdge(dut.dut.dut.core.mesh.idle_o)

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
            core_0   = int(rtl_node.instr_store.core_0_populated_o)
            core_1   = int(rtl_node.instr_store.core_1_populated_o)
            assert core_0 == len(mdl_node.ops), \
                f"{row}, {col}: Expected {len(mdl_node.ops)}, got {core_0}"
            assert core_1 == 0, \
                f"{row}, {col}: Expected 0, got {core_1}"
            # Check the loaded instructions
            dut.info(f"Checking {len(mdl_node.ops)} instructions for {row}, {col}")
            for idx, instr in enumerate(mdl_node.ops):
                got = int(rtl_node.instr_store.ram.memory[idx])
                assert instr.raw == got, \
                    f"Instruction {idx} - {hex(instr.raw)=}, {hex(got)=}"

    # Raise active and let nexus tick
    # - Bit 31 indicates this is a control plane message (not for the mesh)
    # - Bit  0 controls active/inactive status
    dut.info("Enabling nexus")
    dut.inbound.append(AXI4StreamTransaction(data=[0x01, 0x00, 0x00, 0x80]))

    # Wait for all data to be sent
    dut.info("Waiting for AXI4-stream to send all data")
    await dut.inbound.idle()

    # Print out how many nodes are blocked
    rtl_outputs = {}
    for cycle in range(256):
        # Run the model for one tick
        dut.info("Running model until tick")
        env.run(until=mngr.on_tick)
        dut.info("Model reached next tick")

        # Wait for activity
        dut.info("Waiting for idle to fall")
        if dut.dut.dut.core.mesh.idle_o == 1: await FallingEdge(dut.dut.dut.core.mesh.idle_o)

        # Wait for idle (ensuring it is synchronous)
        dut.info("Waiting for idle to rise")
        while True:
            await RisingEdge(dut.dut.dut.core.mesh.idle_o)
            await RisingEdge(dut.clk)
            if dut.dut.dut.core.mesh.idle_o == 1: break

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

        # Check state against the model
        mm_i_curr, mm_i_next, mm_o_curr = 0, 0, 0
        for row, row_entries in enumerate(dut.nodes):
            for col, rtl_node in enumerate(row_entries):
                # Get the RTL state
                ctrl       = rtl_node.entity.control
                rtl_i_curr = int(ctrl.input_curr_q)
                rtl_i_next = int(ctrl.input_next_q)
                rtl_o_curr = int(ctrl.output_last_q)
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
        while dut.outbound._recvQ:
            tran = dut.outbound._recvQ.pop()
            for msg, _ in tran.pack(4):
                is_ctrl = (msg >> 31) & 0x1
                if is_ctrl:
                    payload = msg & ((1 << 31) - 1)
                    dut.info(f"Got control message: 0x{payload:08X}")
                else:
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
