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

from tb_base import TestbenchBase
from drivers.io_common import IORole
from drivers.instr.io import InstrFetchIO, InstrStoreIO
from drivers.instr.fetch import InstrFetchInitiator
from drivers.instr.store import InstrStoreInitiator
from drivers.memory.io import MemoryIO
from drivers.memory.init import MemoryInitiator

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Setup drivers/monitors
        self.load = MemoryInitiator(
            self, self.clk, self.rst, MemoryIO(self.dut, "ld", IORole.RESPONDER),
        )
        self.rd_a = MemoryInitiator(
            self, self.clk, self.rst, MemoryIO(self.dut, "a", IORole.RESPONDER),
        )
        self.rd_b = MemoryInitiator(
            self, self.clk, self.rst, MemoryIO(self.dut, "b", IORole.RESPONDER),
        )

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.load.intf.initialise(IORole.INITIATOR)
        self.rd_a.intf.initialise(IORole.INITIATOR)
        self.rd_b.intf.initialise(IORole.INITIATOR)

class testcase(cocotb.test):
    def __call__(self, dut, *args, **kwargs):
        async def __run_test():
            tb = Testbench(dut)
            await self._func(tb, *args, **kwargs)
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
