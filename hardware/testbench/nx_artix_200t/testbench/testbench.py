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
from drivers.axi4stream.io import AXI4StreamIO
from drivers.axi4stream.init import AXI4StreamInitiator
from drivers.axi4stream.resp import AXI4StreamResponder

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Setup drivers/monitors
        self.ib_ctrl = AXI4StreamInitiator(
            self, self.clk, self.rst,
            AXI4StreamIO(self.dut, "inbound_ctrl", IORole.RESPONDER)
        )
        self.ob_ctrl = AXI4StreamResponder(
            self, self.clk, self.rst,
            AXI4StreamIO(self.dut, "outbound_ctrl", IORole.INITIATOR),
        )
        self.ib_mesh = AXI4StreamInitiator(
            self, self.clk, self.rst,
            AXI4StreamIO(self.dut, "inbound_mesh", IORole.RESPONDER)
        )
        self.ob_mesh = AXI4StreamResponder(
            self, self.clk, self.rst,
            AXI4StreamIO(self.dut, "outbound_mesh", IORole.INITIATOR),
        )
        # Create expected outbound queues
        self.exp_ctrl = []
        self.exp_mesh = []
        # Create a scoreboard
        def compare_ctrl(got):
            exp    = self.exp_ctrl.pop(0)
            all_ok = True
            if len(got.data) != len(exp.data):
                self.error(f"Length differs: {len(got.data) = }, {len(exp.data) = }")
                all_ok = False
            for idx, (got_byte, exp_byte) in enumerate(zip(got.data, exp.data)):
                if got_byte != exp_byte:
                    self.error(f"Byte {idx}: 0x{got_byte:02X} != 0x{exp_byte:02X}")
                    all_ok = False
            assert all_ok, "Comparison error occurred"
        def compare_mesh(got):
            exp = self.exp_mesh.pop(0)
            assert len(got.data) == len(exp.data), \
                f"Length differs: {len(got.data) = }, {len(exp.data) = }"
            for idx, (got_byte, exp_byte) in enumerate(zip(got.data, exp.data)):
                assert got_byte == exp_byte, \
                    f"Byte {idx}: 0x{got_byte:02X} != 0x{exp_byte:02X}"
        self.scoreboard = Scoreboard(self, fail_immediately=False)
        self.scoreboard.add_interface(
            self.ob_ctrl, self.exp_ctrl, compare_fn=compare_ctrl
        )
        self.scoreboard.add_interface(
            self.ob_mesh, self.exp_mesh, compare_fn=compare_mesh
        )

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.ib_ctrl.intf.initialise(IORole.INITIATOR)
        self.ob_ctrl.intf.initialise(IORole.RESPONDER)
        self.ib_mesh.intf.initialise(IORole.INITIATOR)
        self.ob_mesh.intf.initialise(IORole.RESPONDER)

    def start_node_monitors(self):
        """ Create monitor for every node in the mesh on request """
        # Check if node monitors already exist
        if hasattr(self, "nodes") and self.nodes: return
        # Create a monitor for every node in the mesh
        self.nodes = []
        for row in range(int(self.dut.dut.core.ROWS)):
            self.nodes.append(entries := [])
            for col in range(int(self.dut.dut.core.COLUMNS)):
                entries.append(NodeMonitor(
                    self.dut.dut.core.mesh.g_rows[row].g_columns[col].node,
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
            while tb.exp_ctrl: await RisingEdge(tb.clk)
            while tb.exp_mesh: await RisingEdge(tb.clk)
            await ClockCycles(tb.clk, 10)
            raise tb.scoreboard.result
        return cocotb.decorators.RunningTest(__run_test(), self)

def _create_test(func, name, docs, mod, *args, **kwargs):
    """ Custom factory function support """
    async def _my_test(dut): await func(dut, *args, **kwargs)
    _my_test.__name__     = name
    _my_test.__qualname__ = name
    _my_test.__doc__      = docs
    _my_test.__module__   = mod.__name__
    return testcase()(_my_test)

cocotb.regression._create_test = _create_test
