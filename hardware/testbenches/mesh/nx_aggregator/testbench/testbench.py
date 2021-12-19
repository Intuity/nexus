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

import os

import cocotb
from cocotb.triggers import RisingEdge
from cocotb_bus.scoreboard import Scoreboard

from tb_base import TestbenchBase
from drivers.basic.unstrobed import UnstrobedMonitor
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
        self.node_id = self.dut.i_node_id
        self.idle    = self.dut.o_idle
        # Setup drivers/monitors
        self.inbound = StreamInitiator(
            self, self.clk, self.rst,
            StreamIO(self.dut, "inbound", IORole.RESPONDER)
        )
        self.passthrough = StreamInitiator(
            self, self.clk, self.rst,
            StreamIO(self.dut, "passthrough", IORole.RESPONDER)
        )
        self.outbound = StreamResponder(
            self, self.clk, self.rst,
            StreamIO(self.dut, "outbound", IORole.INITIATOR)
        )
        self.outputs = UnstrobedMonitor(
            self, self.clk, self.rst, self.dut.o_outputs
        )
        # Create expected outbound queues
        self.exp_stream = []
        self.exp_output = []
        # Create a scoreboard
        imm_fail = (os.environ.get("FAIL_IMMEDIATELY", "no").lower() == "yes")
        self.scoreboard = Scoreboard(self, fail_immediately=imm_fail)
        self.scoreboard.add_interface(self.outbound, self.exp_stream, reorder_depth=100)
        self.scoreboard.add_interface(self.outputs,  self.exp_output)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.inbound.intf.initialise(IORole.INITIATOR)
        self.passthrough.intf.initialise(IORole.INITIATOR)
        self.outbound.intf.initialise(IORole.RESPONDER)
        self.i_node_id <= 0

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            while tb.exp_stream: await RisingEdge(tb.clk)
            while tb.exp_output: await RisingEdge(tb.clk)
            raise tb.scoreboard.result
        return cocotb.decorators.RunningTest(__run_test(), self)
