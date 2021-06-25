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

from cocotb.triggers import ClockCycles, RisingEdge, FallingEdge
import networkx as nx
import matplotlib.pyplot as plt

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
    loaded = [[0 for y in range(num_cols)] for x in range(num_rows)]
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
                    *common, msg.out_pos, 0, 0, msg.msg_b_row, msg.msg_b_col
                ))
        elif isinstance(msg, LoadInstruction):
            dut.inbound.append(build_load_instr(*common, 0, msg.instr.raw))
            if not msg.broadcast: loaded[msg.tgt_row][msg.tgt_col] += 1
        else:
            raise Exception(f"Unexpected message {msg}")

    # Wait for the inbound driver to drain
    dut.info(f"Waiting for {len(dut.inbound._sendQ)} messages to drain")
    while dut.inbound._sendQ: await RisingEdge(dut.clk)
    while dut.inbound.intf.valid == 1: await RisingEdge(dut.clk)

    # Wait for the idle flag to go high
    if dut.dut.dut.mesh.idle_o == 0: await RisingEdge(dut.dut.dut.mesh.idle_o)

    # Wait for some extra time
    await ClockCycles(dut.clk, 10)

    # Check the instruction counters for every core
    for row in range(num_rows):
        for col in range(num_cols):
            node   = dut.dut.dut.mesh.g_rows[row].g_columns[col].node
            core_0 = int(node.instr_store.core_0_populated_o)
            core_1 = int(node.instr_store.core_1_populated_o)
            assert core_0 == loaded[row][col], \
                f"{row}, {col}: Expected {len(loaded[row][col])}, got {core_0}"
            assert core_1 == 0, \
                f"{row}, {col}: Expected 0, got {core_1}"

    # Start monitoring the mesh
    dut.info("Starting node monitors")
    dut.start_node_monitors()

    # Trigger a single cycle
    dut.info("Triggering a single cycle")
    await RisingEdge(dut.clk)
    dut.active_i <= 1
    await RisingEdge(dut.clk)
    dut.active_i <= 0
    await RisingEdge(dut.clk)

    # Wait for idle
    dut.info("Waiting for idle to fall")
    if dut.dut.dut.mesh.idle_o == 1: await FallingEdge(dut.dut.dut.mesh.idle_o)

    # Print out how many nodes are blocked
    dut.info("Waiting for idle to rise")
    cycle = 0
    while dut.dut.dut.mesh.idle_o == 0:
        await ClockCycles(dut.clk, 1)
        # ib_blocked, ob_blocked = 0, 0
        # for row in dut.nodes:
        #     for node in row:
        #         ib_blocked += 1 if (node.ib_blocked > 0) else 0
        #         ob_blocked += 1 if (node.ob_blocked > 0) else 0
        # dut.info(f"Blocked - Inbound {ib_blocked}, Outbound {ob_blocked}")
        # Search for a deadlock
        graph = nx.DiGraph()
        for row, row_entries in enumerate(dut.nodes):
            for col, _ in enumerate(row_entries):
                graph.add_node((row, col))
        graph.add_node((len(dut.nodes), 0))
        labels = {}
        for row, row_entries in enumerate(dut.nodes):
            for col, node in enumerate(row_entries):
                src  = (row, col)
                tgt  = None
                data = 0
                if node.outbound[0].valid == 1:
                    data = int(node.outbound[0].data)
                    tgt  = (row - 1, col)
                if node.outbound[1].valid == 1:
                    data = int(node.outbound[1].data)
                    tgt  = (row, col + 1)
                if node.outbound[2].valid == 1:
                    data = int(node.outbound[2].data)
                    tgt  = (row + 1, col)
                if node.outbound[3].valid == 1:
                    data = int(node.outbound[3].data)
                    tgt  = (row, col - 1)
                if tgt != None:
                    graph.add_edge(src, tgt)
                    bc    = (data >> 31) & 0x1
                    decay = (data >> 23) & 0xFF
                    tgt_r = (data >> 27) & 0x0F
                    tgt_c = (data >> 23) & 0x0F
                    labels[(src, tgt)] = f"BC {decay}" if bc else f"R {tgt_r}, C {tgt_c}"

        plt.figure(figsize=(8, 8), dpi=100)

        nx.draw(
            graph,
            pos        ={ (x, y): (y, -x) for x, y in graph.nodes() },
            with_labels=True,
            node_shape ="s",
            node_size  =1000,
            node_color ="white",
            edgecolors ="black",
            linewidths =1,
            width      =1,
        )
        nx.draw_networkx_edge_labels(
            graph,
            pos        ={ (x, y): (y, -x) for x, y in graph.nodes() },
            edge_labels=labels,
            label_pos  =0.5,
            font_color ="red",
            font_size  =5,
        )

        # plt.show()
        plt.savefig(f"state_{cycle}.png", dpi=100)
        plt.close()
        cycle += 1
        if cycle > 100: break

    # await RisingEdge(dut.dut.dut.mesh.idle_o)
