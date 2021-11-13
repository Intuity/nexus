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
from types import SimpleNamespace

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge
from cocotb_bus.scoreboard import Scoreboard

from tb_base import TestbenchBase
from drivers.io_common import IORole
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
        # Wrap simple I/Os
        self.status = SimpleNamespace(
            active =dut.o_status_active,
            idle   =dut.o_status_idle,
            trigger=dut.o_status_trigger,
        )
        # Setup drivers/monitors
        self.ctrl_inbound = StreamInitiator(
            self, self.clk, self.rst,
            StreamIO(self.dut, "ctrl_ib", IORole.RESPONDER)
        )
        self.ctrl_outbound = StreamResponder(
            self, self.clk, self.rst,
            StreamIO(self.dut, "ctrl_ob", IORole.INITIATOR),
        )
        self.mesh_inbound = StreamInitiator(
            self, self.clk, self.rst,
            StreamIO(self.dut, "mesh_ib", IORole.RESPONDER)
        )
        self.mesh_outbound = StreamResponder(
            self, self.clk, self.rst,
            StreamIO(self.dut, "mesh_ob", IORole.INITIATOR),
        )
        # Create expected outbound queues
        self.ctrl_expected = []
        self.mesh_expected = []
        # Create a scoreboard
        self.scoreboard = Scoreboard(self, fail_immediately=False)
        self.scoreboard.add_interface(self.ctrl_outbound, self.ctrl_expected, reorder_depth=100)
        self.scoreboard.add_interface(self.mesh_outbound, self.mesh_expected, reorder_depth=100)
        # Setup rapid access to every node in the mesh
        self.nodes = [
            [
                self.dut.u_dut.u_mesh.gen_rows[r].gen_columns[c].u_node
                for c in range(int(dut.COLUMNS))
            ] for r in range(int(dut.ROWS))
        ]

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.ctrl_inbound.intf.initialise(IORole.INITIATOR)
        self.ctrl_outbound.intf.initialise(IORole.RESPONDER)
        self.mesh_inbound.intf.initialise(IORole.INITIATOR)
        self.mesh_outbound.intf.initialise(IORole.RESPONDER)

    @property
    def base_dir(self): return Path(__file__).absolute().parent

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            while tb.ctrl_expected: await RisingEdge(tb.clk)
            while tb.mesh_expected: await RisingEdge(tb.clk)
            await ClockCycles(tb.clk, 10)
            raise tb.scoreboard.result
        return cocotb.decorators.RunningTest(__run_test(), self)
