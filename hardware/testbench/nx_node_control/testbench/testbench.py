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
from cocotb_bus.scoreboard import Scoreboard
from cocotb.triggers import ClockCycles, RisingEdge

from tb_base import TestbenchBase
from drivers.io_common import IORole
from drivers.map_io.io import IOMapIO
from drivers.map_io.driver import IOMapInitiator
from drivers.state.io import StateIO
from drivers.state.driver import StateInitiator
from drivers.stream.io import StreamIO
from drivers.stream.resp import StreamResponder
from drivers.memory.io import MemoryIO
from drivers.memory.resp import MemoryResponder

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Pickup signals
        self.ext_trigger = dut.trigger_i
        self.trigger     = dut.core_trigger_o
        self.inputs      = dut.core_inputs_o
        self.outputs     = dut.core_outputs_i
        self.grant       = dut.token_grant_i
        self.release     = dut.token_release_o
        # Setup drivers/monitors
        self.msg = StreamResponder(
            self, self.clk, self.rst, StreamIO(self.dut, "msg", IORole.INITIATOR),
        )
        self.io = IOMapInitiator(
            self, self.clk, self.rst, IOMapIO(self.dut, "map", IORole.RESPONDER),
        )
        self.signal = StateInitiator(
            self, self.clk, self.rst, StateIO(self.dut, "signal", IORole.RESPONDER),
        )
        self.memory = MemoryResponder(
            self, self.clk, self.rst, MemoryIO(self.dut, "store", IORole.INITIATOR),
        )
        # Create queues for expected transactions
        self.exp_msg = []
        # Create a scoreboard
        self.scoreboard = Scoreboard(self, fail_immediately=False)
        self.scoreboard.add_interface(self.msg, self.exp_msg)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.ext_trigger <= 0
        self.outputs     <= 0
        self.grant       <= 0
        self.release     <= 0
        self.node_row_i  <= 0
        self.node_col_i  <= 0
        self.msg.intf.initialise(IORole.RESPONDER)
        self.io.intf.initialise(IORole.INITIATOR)
        self.signal.intf.initialise(IORole.INITIATOR)
        self.memory.intf.initialise(IORole.RESPONDER)

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
