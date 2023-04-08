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

import os
from random import randint
from types import SimpleNamespace

from forastero import BaseBench, IORole

import nxmodel
from drivers.stream.io import StreamIO
from drivers.stream.common import StreamTransaction
from drivers.stream.init import StreamInitiator
from drivers.stream.resp import StreamResponder
from nxconstants import NodeID
from nxmodel import Nexus, direction_t, NXMessagePipe, NXNode, node_raw_t, pack_node_raw, unpack_node_raw

class Testbench(BaseBench):

    def __init__(self, dut):
        """ Initialise the testbench.

        Args:
            dut: Pointer to the DUT
        """
        super().__init__(dut, clk="clk", rst="rst")
        # Wrap I/Os
        self.status = SimpleNamespace(active =self.dut.o_status_active,
                                      idle   =self.dut.o_status_idle,
                                      trigger=self.dut.o_status_trigger)
        # Register inbound/outbound control streams
        self.register_driver("inbound",
                             StreamInitiator(self,
                                             self.clk,
                                             self.rst,
                                             StreamIO(self.dut, "ctrl_in", IORole.RESPONDER)))
        self.register_monitor("outbound",
                              StreamResponder(self,
                                              self.clk,
                                              self.rst,
                                              StreamIO(self.dut, "ctrl_out", IORole.INITIATOR)))
        # Create model instance
        if os.environ.get("NXMODEL_LOGGING", "no") == "yes":
            nxmodel.setup_logging(True)
        self.model          = Nexus(int(self.dut.u_dut.ROWS.value),
                                    int(self.dut.u_dut.COLUMNS.value))
        self.model_inbound  = self.model.get_ingress()
        self.model_outbound = self.model.get_egress()

    async def initialise(self):
        """ Initialise the DUT's I/O """
        await super().initialise()
        self.model.reset()
