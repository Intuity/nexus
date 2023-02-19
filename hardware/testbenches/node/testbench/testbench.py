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

from types import SimpleNamespace

from forastero import BaseBench, IORole

from drivers.stream.io import StreamIO
from drivers.stream.init import StreamInitiator
from drivers.stream.resp import StreamResponder
from nxmodel import NXNode

class Testbench(BaseBench):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut, clk="clk", rst="rst")
        # Wrap I/Os
        self.node_id = self.dut.i_node_id
        self.trigger = SimpleNamespace(input =self.dut.i_trigger,
                                       output=self.dut.o_trigger)
        self.idle    = SimpleNamespace(input =self.dut.i_idle,
                                       output=self.dut.o_idle)
        # Register message interface initiator & responder drivers
        for dirx in ("north", "east", "south", "west"):
            self.register_driver(f"ib_{dirx}",
                                 StreamInitiator(self,
                                                 self.clk,
                                                 self.rst,
                                                 StreamIO(self.dut,
                                                          f"ib_{dirx}",
                                                          IORole.RESPONDER)))
            self.register_monitor(f"ob_{dirx}",
                                  StreamResponder(self,
                                                  self.clk,
                                                  self.rst,
                                                  StreamIO(self.dut,
                                                           f"ob_{dirx}",
                                                           IORole.INITIATOR)))
        # Create model instance
        self.model = NXNode(0, 0, False)

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.node_id.value       = 0
        self.idle.input.value    = 1
        self.trigger.input.value = 0
        self.model.reset()
