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
        # Setup drivers/monitors
        self.inbound = StreamInitiator(
            self, self.clk, self.rst,
            StreamIO(self.dut, "inbound", IORole.RESPONDER),
        )
        self.north = StreamResponder(
            self, self.clk, self.rst,
            StreamIO(self.dut, "north", IORole.INITIATOR), name="north",
        )
        self.east = StreamResponder(
            self, self.clk, self.rst,
            StreamIO(self.dut, "east", IORole.INITIATOR), name="east",
        )
        self.south = StreamResponder(
            self, self.clk, self.rst,
            StreamIO(self.dut, "south", IORole.INITIATOR), name="south",
        )
        self.west = StreamResponder(
            self, self.clk, self.rst,
            StreamIO(self.dut, "west", IORole.INITIATOR), name="west",
        )
        # Create a queue for expected messages
        self.exp_north = []
        self.exp_east  = []
        self.exp_south = []
        self.exp_west  = []
        # Create a scoreboard
        self.scoreboard = Scoreboard(self, fail_immediately=False)
        self.scoreboard.add_interface(self.north, self.exp_north)
        self.scoreboard.add_interface(self.east,  self.exp_east )
        self.scoreboard.add_interface(self.south, self.exp_south)
        self.scoreboard.add_interface(self.west,  self.exp_west )

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.inbound.intf.initialise(IORole.INITIATOR)
        self.north.intf.initialise(IORole.RESPONDER)
        self.east.intf.initialise(IORole.RESPONDER)
        self.south.intf.initialise(IORole.RESPONDER)
        self.west.intf.initialise(IORole.RESPONDER)

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            while tb.exp_north: await RisingEdge(tb.clk)
            while tb.exp_east : await RisingEdge(tb.clk)
            while tb.exp_south: await RisingEdge(tb.clk)
            while tb.exp_west : await RisingEdge(tb.clk)
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
