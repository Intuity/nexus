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

from pathlib import Path

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge
from cocotb_bus.scoreboard import Scoreboard
import matplotlib.pyplot as plt
import networkx as nx

from tb_base import TestbenchBase
from drivers.io_common import IORole
from drivers.node.monitor import NodeMonitor
from drivers.stream.io import StreamIO
from drivers.stream.init import StreamInitiator
from drivers.stream.resp import StreamResponder

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Setup drivers/monitors
        self.inbound = StreamInitiator(
            self, self.clk, self.rst,
            StreamIO(self.dut, "inbound", IORole.RESPONDER)
        )
        self.outbound = StreamResponder(
            self, self.clk, self.rst,
            StreamIO(self.dut, "outbound", IORole.INITIATOR),
        )
        # Create expected outbound queues
        self.expected = []
        # Create a scoreboard
        self.scoreboard = Scoreboard(self, fail_immediately=False)
        self.scoreboard.add_interface(self.outbound, self.expected, reorder_depth=100)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.inbound.intf.initialise(IORole.INITIATOR)
        self.outbound.intf.initialise(IORole.RESPONDER)
        self.active_i <= 0

    def start_node_monitors(self):
        """ Create monitor for every node in the mesh on request """
        # Check if node monitors already exist
        if hasattr(self, "nodes") and self.nodes: return
        # Create a monitor for every node in the mesh
        self.nodes = []
        for row in range(int(self.dut.dut.ROWS)):
            self.nodes.append(entries := [])
            for col in range(int(self.dut.dut.COLUMNS)):
                entries.append(NodeMonitor(
                    self.dut.dut.mesh.g_rows[row].g_columns[col].node,
                    self.clk, self.rst, name=f"row_{row}_col_{col}"
                ))

    def plot_mesh_state(self, path):
        """ Plot the state of the mesh using NetworkX.

        Args:
            path: Path to write the rendered image to
        """
        # If node monitors don't exist, create them
        if not hasattr(self, "nodes") or not self.nodes:
            self.start_node_monitors()
        # Create each node in the mesh
        graph = nx.DiGraph()
        for row, row_entries in enumerate(self.nodes):
            for col, _ in enumerate(row_entries):
                graph.add_node((row, col))
        # Create the output message node
        graph.add_node((len(self.nodes), 0))
        # Add all of the edges (representing messages)
        labels = {}
        for row, row_entries in enumerate(self.nodes):
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
        # Setup the Matplotlib plot
        plt.figure(figsize=(8, 8), dpi=100)
        # Draw the graph
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
        # Label the edges
        nx.draw_networkx_edge_labels(
            graph,
            pos        ={ (x, y): (y, -x) for x, y in graph.nodes() },
            edge_labels=labels,
            label_pos  =0.5,
            font_color ="red",
            font_size  =5,
        )
        # Write out to file
        plt.savefig(path, dpi=100)
        # Clean up
        plt.close()

    @property
    def base_dir(self): return Path(__file__).absolute().parent

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            while tb.expected: await RisingEdge(tb.clk)
            await ClockCycles(tb.clk, 10)
            raise tb.scoreboard.result
        return cocotb.decorators.RunningTest(__run_test(), self)
