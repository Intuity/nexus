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

from pathlib import Path
from types import SimpleNamespace

import cocotb
from cocotb.triggers import ClockCycles, RisingEdge
from cocotb_bus.scoreboard import Scoreboard

from nxconstants import ControlRespType, ControlResponsePadding

from tb_base import TestbenchBase
from drivers.io_common import IORole
from drivers.axi4stream.io import AXI4StreamIO
from drivers.axi4stream.init import AXI4StreamInitiator
from drivers.axi4stream.resp import AXI4StreamResponder

class Testbench(TestbenchBase):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut)
        # Wrap simple I/Os
        self.status = SimpleNamespace(
            active =dut.o_status_active,
            idle   =dut.o_status_idle,
            trigger=dut.o_status_trigger,
        )
        # Setup drivers/monitors
        self.inbound = AXI4StreamInitiator(
            self, self.clk, self.rst,
            AXI4StreamIO(self.dut, "inbound", IORole.RESPONDER)
        )
        self.outbound = AXI4StreamResponder(
            self, self.clk, self.rst,
            AXI4StreamIO(self.dut, "outbound", IORole.INITIATOR),
        )
        # Create expected outbound queues
        self.expected = []
        # Create a scoreboard
        def compare(got):
            # Split the stream into 16-byte (128-bit) chunks and compare
            all_data = got.data[:]
            while all_data:
                # Take the next chunk of received data
                got_chunk = sum([(x << (n * 8)) for n, x in enumerate(all_data[:16])])
                all_data = all_data[16:]
                # Ignore padding packets
                # NOTE: Once a padding packet has been seen, the rest in this
                #       transaction will all be padding as well!
                pkt = ControlResponsePadding()
                pkt.unpack(got_chunk)
                if pkt.format == ControlRespType.PADDING: break
                # Take the next chunk of expected data
                exp_chunk = sum([(x << (n * 8)) for n, x in enumerate(self.expected[0].data[:16])])
                self.expected[0].data = self.expected[0].data[16:]
                if len(self.expected[0].data) == 0: self.expected.pop(0)
                # Compare
                assert got_chunk == exp_chunk, \
                    f"Got: 0x{got_chunk:032X}, Exp: 0x{exp_chunk:032X}"
        self.scoreboard = Scoreboard(self, fail_immediately=False)
        self.scoreboard.add_interface(
            self.outbound, self.expected, compare_fn=compare
        )
        # Setup rapid access to every node in the mesh
        self.nodes = [
            [
                self.dut.u_dut.u_nexus.u_mesh.gen_rows[r].gen_columns[c].u_node
                for c in range(int(dut.u_dut.u_nexus.COLUMNS))
            ] for r in range(int(dut.u_dut.u_nexus.ROWS))
        ]

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.inbound.intf.initialise(IORole.INITIATOR)
        self.outbound.intf.initialise(IORole.RESPONDER)

    @property
    def base_dir(self): return Path(__file__).absolute().parent

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
