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
        # Wrap I/Os
        self.soft_reset   = self.dut.o_soft_reset
        self.node_idle    = self.dut.i_mesh_node_idle
        self.agg_idle     = self.dut.i_mesh_agg_idle
        self.mesh_trigger = self.dut.o_mesh_trigger
        self.mesh_outputs = self.dut.i_mesh_outputs
        self.status       = SimpleNamespace(
            active =self.dut.o_status_active,
            idle   =self.dut.o_status_idle,
            trigger=self.dut.o_status_trigger,
        )
        # Setup drivers/monitors
        self.ctrl_in = StreamInitiator(
            self, self.clk, self.rst, StreamIO(self.dut, "ctrl_in", IORole.RESPONDER),
        )
        self.ctrl_out = StreamResponder(
            self, self.clk, self.rst, StreamIO(self.dut, "ctrl_out", IORole.INITIATOR),
        )
        self.mesh_in = StreamResponder(
            self, self.clk, self.rst, StreamIO(self.dut, "mesh_in", IORole.INITIATOR),
        )
        self.mesh_out = StreamInitiator(
            self, self.clk, self.rst, StreamIO(self.dut, "mesh_out", IORole.RESPONDER),
        )
        # Create queues for expected transactions
        self.exp_ctrl = []
        self.exp_mesh = []
        # Create a scoreboard
        self.scoreboard = Scoreboard(self, fail_immediately=True)
        self.scoreboard.add_interface(self.ctrl_out, self.exp_ctrl)
        self.scoreboard.add_interface(self.mesh_in, self.exp_mesh)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.ctrl_in.intf.initialise(IORole.INITIATOR)
        self.ctrl_out.intf.initialise(IORole.RESPONDER)
        self.mesh_in.intf.initialise(IORole.RESPONDER)
        self.mesh_out.intf.initialise(IORole.INITIATOR)
        self.node_idle    <= ((1 << int(self.dut.COLUMNS)) - 1)
        self.agg_idle     <= 1
        self.mesh_outputs <= 0

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
