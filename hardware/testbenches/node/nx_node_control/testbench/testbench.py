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
from cocotb_bus.scoreboard import Scoreboard
from cocotb.triggers import ClockCycles, RisingEdge

from tb_base import TestbenchBase
from drivers.io_common import IORole
from drivers.memory.io import MemoryIO
from drivers.memory.resp import MemoryResponder
from drivers.state.io import StateIO
from drivers.state.driver import StateInitiator
from drivers.stream.io import StreamIO
from drivers.stream.resp import StreamResponder

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Basic interfaces
        self.trigger      = self.dut.i_trigger
        self.idle         = self.dut.o_idle
        self.lb_mask      = self.dut.i_loopback_mask
        self.num_instr    = self.dut.i_num_instr
        self.core_inputs  = self.dut.o_core_inputs
        self.core_outputs = self.dut.i_core_outputs
        self.core_trigger = self.dut.o_core_trigger
        # Setup drivers/monitors
        self.input = StateInitiator(
            self, self.clk, self.rst, StateIO(self.dut, "input", IORole.RESPONDER),
        )
        self.msg = StreamResponder(
            self, self.clk, self.rst, StreamIO(self.dut, "msg", IORole.INITIATOR),
        )
        self.ram = MemoryResponder(
            self, self.clk, self.rst, MemoryIO(self.dut, "ram", IORole.INITIATOR),
        )
        # Create queues for expected transactions
        self.exp_msg = []
        # Create a scoreboard
        imm_fail = (os.environ.get("FAIL_IMMEDIATELY", "no").lower() == "yes")
        self.scoreboard = Scoreboard(self, fail_immediately=imm_fail)
        self.scoreboard.add_interface(self.msg, self.exp_msg)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        # Basic interfaces
        self.trigger      <= 0
        self.lb_mask      <= 0
        self.num_instr    <= 0
        self.core_outputs <= 0
        # Drivers/monitors
        self.input.intf.initialise(IORole.INITIATOR)
        self.msg.intf.initialise(IORole.RESPONDER)
        self.ram.intf.initialise(IORole.RESPONDER)

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            while tb.exp_msg: await RisingEdge(tb.clk)
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
