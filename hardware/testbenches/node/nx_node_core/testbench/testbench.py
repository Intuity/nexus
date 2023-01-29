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

from tb_base import TestbenchBase
from drivers.io_common import IORole
from drivers.memory.io import MemoryIO
from drivers.memory.resp import MemoryResponder

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Basic interfaces
        self.inputs    = self.dut.i_inputs
        self.outputs   = self.dut.o_outputs
        self.populated = self.dut.i_populated
        self.trigger   = self.dut.i_trigger
        self.idle      = self.dut.o_idle
        # Wrap complex interfaces
        self.ram = MemoryResponder(
            self,
            self.clk,
            self.rst,
            MemoryIO(self.dut, "instr", IORole.INITIATOR),
            delay=2,
        )

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.inputs    <= 0
        self.populated <= 0
        self.trigger   <= 0
        self.ram.intf.initialise(IORole.RESPONDER)

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
            # while tb.model.results: RisingEdge(tb.clk)
            # raise tb.scoreboard.result
        return cocotb.decorators.RunningTest(__run_test(), self)
