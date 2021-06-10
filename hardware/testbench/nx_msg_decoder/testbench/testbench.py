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

from .monitors.instr_load_mon import InstrLoadIO, InstrLoadMon
from .monitors.io_map_mon import IOMapIO, IOMapMon
from .monitors.state_mon import StateIO, StateMon

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Wrap complex interfaces
        self.msg_io    = StreamIO(self.dut, "msg",    IORole.RESPONDER)
        self.bypass_io = StreamIO(self.dut, "bypass", IORole.INITIATOR)
        # Setup drivers/monitors
        self.msg    = StreamInitiator(self, self.clk, self.rst, self.msg_io)
        self.bypass = StreamResponder(self, self.clk, self.rst, self.bypass_io)
        self.instr_load = InstrLoadMon(
            self, self.clk, self.rst, InstrLoadIO(self.dut, "instr", IORole.INITIATOR),
        )
        self.io_map = IOMapMon(
            self, self.clk, self.rst, IOMapIO(self.dut, "map", IORole.INITIATOR),
        )
        self.state = StateMon(
            self, self.clk, self.rst, StateIO(self.dut, "signal", IORole.INITIATOR),
        )
        # Create queues for expected transactions
        self.exp_bypass = []
        self.exp_instr  = []
        self.exp_io     = []
        self.exp_state  = []
        # Create a scoreboard
        self.scoreboard = Scoreboard(self, fail_immediately=False)
        self.scoreboard.add_interface(self.bypass,     self.exp_bypass)
        self.scoreboard.add_interface(self.instr_load, self.exp_instr)
        self.scoreboard.add_interface(self.io_map,     self.exp_io)
        self.scoreboard.add_interface(self.state,      self.exp_state)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.node_col_i <= 0
        self.node_row_i <= 0
        self.msg_io.initialise(IORole.INITIATOR)
        self.bypass_io.initialise(IORole.RESPONDER)

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            while tb.exp_bypass: await RisingEdge(tb.clk)
            while tb.exp_instr : await RisingEdge(tb.clk)
            while tb.exp_io    : await RisingEdge(tb.clk)
            while tb.exp_state : await RisingEdge(tb.clk)
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
