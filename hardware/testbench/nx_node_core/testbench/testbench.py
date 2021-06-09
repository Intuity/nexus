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
from cocotb.triggers import RisingEdge

from tb_base import TestbenchBase
from drivers.io_common import IORole
from drivers.instr_io import InstrIO
from drivers.instr_store import InstrStore

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Wrap complex interfaces
        self.instr = InstrIO(self.dut, "instr", IORole.INITIATOR)
        # Setup drivers/monitors
        self.instr_store = InstrStore(self, self.clk, self.rst, self.instr)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.inputs_i      <= 0
        self.populated_i   <= 0
        self.trigger_i     <= 0
        self.instr.initialise(IORole.RESPONDER)

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            # while tb.model.results: RisingEdge(tb.clk)
            # raise tb.scoreboard.result
        return cocotb.decorators.RunningTest(__run_test(), self)
