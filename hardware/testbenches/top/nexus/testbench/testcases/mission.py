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

from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge
from cocotb.utils import get_sim_time

from nxconstants import (NodeCommand, NodeID, NodeMessage, NodeParameter,
                         ControlCommand, ControlSetActive)
from nxloader import NXLoader
from nxmodel import Nexus

from drivers.stream.common import StreamTransaction
from node.load import load_data, load_loopback, load_parameter

from ..testbench import testcase

@testcase()
async def mission_mode(dut):
    """ Load up and run a real design """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Determine parameters
    num_rows    = int(dut.ROWS)
    num_cols    = int(dut.COLUMNS)
    node_inputs = int(dut.INPUTS)
    ram_data_w  = int(dut.RAM_DATA_W)
    dut.info(f"Mesh size - rows {num_rows}, columns {num_cols}")

    # Disable scoreboarding of output
    dut.mesh_outbound._callbacks = []

    # Work out the full path
    full_path = dut.base_dir / "data" / "design.json"

    # Create an instance of NXModel
    model = Nexus(num_rows, num_cols)

    # Load the design using the Python loader
    design = NXLoader(full_path)

    # Load data into the mesh
    for idx_row, row_state in enumerate(design.state):
        for idx_col, node in enumerate(row_state):
            node_id = NodeID(row=idx_row, column=idx_col)
            # Load instructions, lookup table, and output mappings
            load_data(
                inbound   =dut.mesh_inbound,
                node_id   =node_id,
                ram_data_w=ram_data_w,
                stream    =[x.pack() for x in (node.instructions + node.lookup + node.mappings)],
                model     =model.get_ingress(),
            )
            # Program the loopback
            load_loopback(
                inbound   =dut.mesh_inbound,
                node_id   =node_id,
                num_inputs=node_inputs,
                mask      =node.loopback,
                model     =model.get_ingress(),
            )
            # Set parameters
            for key, value in (
                (NodeParameter.INSTRUCTIONS, len(node.instructions)),
                (NodeParameter.OUTPUTS,      len(node.lookup      )),
            ):
                load_parameter(
                    dut.mesh_inbound, node_id, key, value, model.get_ingress()
                )

    # Wait for the inbound driver to drain
    dut.info(f"Waiting for {len(dut.mesh_inbound._sendQ)} messages to drain")
    await dut.mesh_inbound.idle()

    # Wait for the idle flag to go high
    if dut.status.idle == 0: await RisingEdge(dut.status.idle)
    await ClockCycles(dut.clk, 10)

    # Check the next load address for every core
    for row, col in product(range(num_rows), range(num_cols)):
        state   = design.state[row][col]
        exp_val = len(state.instructions + state.lookup + state.mappings)
        rtl_val = int(dut.nodes[row][col].u_decoder.load_address_q)
        dut.info(f"Checking node {row}, {col} has loaded {exp_val} entries")
        assert rtl_val == exp_val, f"{row}, {col}: RTL {rtl_val} != EXP {exp_val}"

    # Raise active and let nexus tick
    dut.info("Enabling nexus")
    dut.ctrl_inbound.append(StreamTransaction(
        ControlSetActive(command=ControlCommand.ACTIVE, active=1).pack()
    ))

    # Capture start time
    tick_count = 300
    clk_period = 2
    start_time = get_sim_time(units="ns")

    # Compare RTL against the model tick by tick
    rtl_outputs, mdl_outputs = {}, {}
    for cycle in range(tick_count):
        def cycdebug(msg): dut.debug(f"[{cycle:4d}] {msg}")
        def cycinfo(msg): dut.info(f"[{cycle:4d}] {msg}")
        def cycwarn(msg): dut.warning(f"[{cycle:4d}] {msg}")

        # Run the model for one tick
        if (cycle % 10) == 0: cycinfo("Starting cycle")
        model.run(1)

        # Wait for activity
        cycdebug("Waiting for idle to fall")
        if dut.status.idle == 1: await FallingEdge(dut.status.idle)

        # Wait for idle (ensuring it is synchronous)
        cycdebug("Waiting for idle to rise")
        while dut.status.idle == 0: await RisingEdge(dut.clk)

        # Run through every node and column
        mismatches = 0
        for row, col in product(range(num_rows), range(num_cols)):
            rtl_node = dut.nodes[row][col]
            mdl_node = model.get_mesh().get_node(row, col)
            # Pickup RTL node I/O
            rtl_i_curr = int(rtl_node.u_control.u_inputs.inputs_curr_q)
            rtl_i_next = int(rtl_node.u_control.u_inputs.inputs_next_q)
            rtl_o_curr = int(rtl_node.u_core.o_outputs)
            cycdebug(
                f"{row}, {col} - Inputs Current: 0x{rtl_i_curr:08X}, "
                f"Inputs Next: 0x{rtl_i_next:08X}, Outputs: 0x{rtl_o_curr:08X}"
            )
            # Pickup model node I/O
            mdl_i_curr = sum((x << i) for i, x in mdl_node.get_current_inputs().items())
            mdl_i_next = sum((x << i) for i, x in mdl_node.get_next_inputs().items())
            mdl_o_curr = sum((x << i) for i, x in mdl_node.get_current_outputs().items())
            # Mask input next with the loopback mask
            mask        = ((1 << node_inputs) - 1) - design.state[row][col].loopback
            rtl_i_next &= mask
            mdl_i_next &= mask
            # Compare RTL against model
            for label, rtl_val, mdl_val in (
                ("Input Current ", rtl_i_curr, mdl_i_curr),
                ("Input Next    ", rtl_i_next, mdl_i_next),
                ("Output Current", rtl_o_curr, mdl_o_curr),
            ):
                # Skip instances where RTL and model match
                if rtl_val == mdl_val: continue
                # Increment count of mismatches and log a warning
                mismatches += 1
                cycwarn(
                    f"{row}, {col} - {label}: RTL 0x{rtl_val:08X} != MDL: 0x{mdl_val:08X}"
                )

        # Accumulate updated RTL output state
        while dut.mesh_outbound._recvQ:
            tran = dut.mesh_outbound._recvQ.popleft()
            msg  = NodeMessage()
            msg.unpack(tran.data)
            if msg.raw.header.command != NodeCommand.SIGNAL: continue
            rtl_outputs[
                msg.signal.header.row,
                msg.signal.header.column,
                msg.signal.index
            ] = msg.signal.state

        # Accumulate updated model output state
        for key, val in model.pop_output().items():
            mdl_outputs[key] = val

        # Cross check RTL against model state
        for key in set(list(rtl_outputs.keys()) + list(mdl_outputs.keys())):
            rtl_val = rtl_outputs.get(key, 0)
            mdl_val = mdl_outputs.get(key, 0)
            # Skip instances where RTL and model match
            if rtl_val == mdl_val: continue
            # Increment count of mismatches and log a warning
            mismatches += 1
            cycwarn(
                f"{row}, {col} - output {key}: RTL {rtl_val} != MDL {mdl_val}"
            )

        # Check for mismatches
        assert mismatches == 0, f"Detected {mismatches} between RTL and model"
        continue

    # Calculate simulation rate
    delta      = get_sim_time(units="ns") - start_time
    num_cycles = delta / clk_period
    cyc_per_tk = num_cycles / tick_count
    dut.info(f"Achieved {cyc_per_tk:.02f} cycles/tick - if mesh clock...")
    for tgt_period in (2, 4, 8):
        clk_frequency  = (1 / (tgt_period * 1E-9)) / 1E6
        time_per_tick  = cyc_per_tk * tgt_period
        tick_frequency = (1 / (time_per_tick * 1E-9)) / 1E6
        dut.info(
            f" - @{clk_frequency:.02f} MHz -> {tick_frequency:.02f} MHz simulated"
        )

