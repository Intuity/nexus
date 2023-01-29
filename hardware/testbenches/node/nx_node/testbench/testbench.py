# Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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
from types import SimpleNamespace

import cocotb
from cocotb.triggers import RisingEdge
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
        self.node_id       = self.dut.i_node_id
        self.trigger       = self.dut.i_trigger
        self.idle          = SimpleNamespace(
            input =self.dut.i_idle,
            output=self.dut.o_idle,
        )
        self.ext_inputs_en = self.dut.i_ext_inputs_en
        self.ext_inputs    = self.dut.i_ext_inputs
        self.present       = [
            self.dut.i_ob_north_present, self.dut.i_ob_east_present,
            self.dut.i_ob_south_present, self.dut.i_ob_west_present,
        ]
        # Setup drivers/monitors
        self.inbound = [
            StreamInitiator(
                self, self.clk, self.rst,
                StreamIO(self.dut, dirx, IORole.RESPONDER)
            ) for dirx in ("ib_north", "ib_east", "ib_south", "ib_west")
        ]
        self.outbound = [
            StreamResponder(
                self, self.clk, self.rst,
                StreamIO(self.dut, dirx, IORole.INITIATOR), name=dirx,
            ) for dirx in ("ob_north", "ob_east", "ob_south", "ob_west")
        ]
        # Create expected outbound queues
        self.expected = [[] for _ in self.outbound]
        # Create a scoreboard
        imm_fail = (os.environ.get("FAIL_IMMEDIATELY", "no").lower() == "yes")
        self.scoreboard = Scoreboard(self, fail_immediately=imm_fail)
        for resp, exp in zip(self.outbound, self.expected):
            self.scoreboard.add_interface(resp, exp, reorder_depth=100)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        for init in self.inbound : init.intf.initialise(IORole.INITIATOR)
        for resp in self.outbound: resp.intf.initialise(IORole.RESPONDER)
        for flag in self.present : flag <= 1
        self.idle.input    <= 1
        self.trigger       <= 0
        self.node_id       <= 0
        self.ext_inputs_en <= 0
        self.ext_inputs    <= 0

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            for idx, exp in enumerate(tb.expected):
                while exp: await RisingEdge(tb.clk)
                tb.info(f"Exhausted queue {idx}")
            raise tb.scoreboard.result
        return cocotb.decorators.RunningTest(__run_test(), self)
