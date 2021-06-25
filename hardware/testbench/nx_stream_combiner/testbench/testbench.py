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
        self.stream_a = StreamInitiator(
            self, self.clk, self.rst, StreamIO(self.dut, "stream_a", IORole.RESPONDER)
        )
        self.stream_b = StreamInitiator(
            self, self.clk, self.rst, StreamIO(self.dut, "stream_b", IORole.RESPONDER)
        )
        self.comb     = StreamResponder(
            self, self.clk, self.rst, StreamIO(self.dut, "comb", IORole.INITIATOR)
        )
        # Create a queue for expected messages
        self.expected = []
        # Create a scoreboard
        self.scoreboard = Scoreboard(self, fail_immediately=False)
        def find_exp(tran):
            # Set the maximum length to search to based on arbitration scheme
            if dut.dut.ARB_SCHEME.value.decode("utf-8") == "round_robin":
                search_to = min(3, len(self.expected))
            else:
                search_to = len(self.expected)
            # Search for the entry
            for i in range(search_to):
                if self.expected[i] == tran: break
            else:
                i = 0
            return self.expected.pop(i)
        self.scoreboard.add_interface(self.comb, find_exp, reorder_depth=2)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.stream_a.intf.initialise(IORole.INITIATOR)
        self.stream_b.intf.initialise(IORole.INITIATOR)
        self.comb.intf.initialise(IORole.RESPONDER)

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            while tb.expected: await RisingEdge(tb.clk)
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
