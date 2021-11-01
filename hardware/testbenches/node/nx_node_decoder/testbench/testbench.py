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
from drivers.basic.unstrobed import UnstrobedMonitor
from drivers.io_common import IORole
from drivers.memory.io import MemoryIO
from drivers.memory.monitor import MemoryMonitor
from drivers.state.io import StateIO
from drivers.state.monitor import StateMonitor
from drivers.stream.io import StreamIO
from drivers.stream.init import StreamInitiator

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Setup drivers for complex interfaces
        self.msg = StreamInitiator(
            self, self.clk, self.rst, StreamIO(self.dut, "msg", IORole.RESPONDER)
        )
        self.ram = MemoryMonitor(
            self, self.clk, self.rst, MemoryIO(self.dut, "ram", IORole.INITIATOR)
        )
        self.sig = StateMonitor(
            self, self.clk, self.rst, StateIO(self.dut, "input", IORole.INITIATOR)
        )
        # Pickup simple interfaces
        self.idle       = self.dut.o_idle
        self.lb_mask    = UnstrobedMonitor(
            self, self.clk, self.rst, self.dut.o_loopback_mask, name="lb_mask"
        )
        self.num_instr  = UnstrobedMonitor(
            self, self.clk, self.rst, self.dut.o_num_instr, name="num_instr"
        )
        self.num_output = UnstrobedMonitor(
            self, self.clk, self.rst, self.dut.o_num_output, name="num_output"
        )
        # Create queues for expected transactions
        self.exp_ram        = []
        self.exp_sig        = []
        self.exp_lb_mask    = []
        self.exp_num_instr  = []
        self.exp_num_output = []
        # Create a scoreboard
        self.scoreboard = Scoreboard(self) # , fail_immediately=False)
        self.scoreboard.add_interface(self.ram,        self.exp_ram       )
        self.scoreboard.add_interface(self.sig,        self.exp_sig       )
        self.scoreboard.add_interface(self.lb_mask,    self.exp_lb_mask   )
        self.scoreboard.add_interface(self.num_instr,  self.exp_num_instr )
        self.scoreboard.add_interface(self.num_output, self.exp_num_output)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.msg.intf.initialise(IORole.INITIATOR)
        self.ram.intf.initialise(IORole.RESPONDER)
        self.sig.intf.initialise(IORole.RESPONDER)

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            while tb.exp_ram       : await RisingEdge(tb.clk)
            while tb.exp_sig       : await RisingEdge(tb.clk)
            while tb.exp_lb_mask   : await RisingEdge(tb.clk)
            while tb.exp_num_instr : await RisingEdge(tb.clk)
            while tb.exp_num_output: await RisingEdge(tb.clk)
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
