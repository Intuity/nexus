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

from cocotb_bus.monitors import Monitor
from cocotb.triggers import RisingEdge, ClockCycles

from ..io_common import IORole
from ..stream.io import StreamIO

class NodeMonitor(Monitor):
    """ Monitors the status of a node in the mesh """

    def __init__(self, entity, clock, reset, name="NodeMonitor"):
        """ Initialise the NodeMonitor instance.

        Args:
            entity     : Pointer to the testbench/DUT
            clock      : Clock signal for the interface
            reset      : Reset signal for the interface
            intf       : Interface
            name       : Optional name of the driver (defaults to NodeMonitor)
        """
        self.name     = name
        self.entity   = entity
        self.clock    = clock
        self.reset    = reset
        self.inbound  = [StreamIO(entity, x, IORole.RESPONDER) for x in (
            "ib_north", "ib_east", "ib_south", "ib_west",
        )]
        self.outbound = [StreamIO(entity, x, IORole.INITIATOR) for x in (
            "ob_north", "ob_east", "ob_south", "ob_west",
        )]
        self.ib_active  = [False] * 4
        self.ob_active  = [False] * 4
        self.ib_blocked = 0
        self.ob_blocked = 0
        super().__init__()

    async def _monitor_recv(self):
        """ Monitor the outbound interfaces of the node """
        while True:
            # Wait for the next clock edge
            await RisingEdge(self.clock)
            # Skip when reset active
            if self.reset == 1: continue
            # Determine which interfaces are active
            self.ib_blocked = 0
            self.ob_blocked = 0
            for idx, intf in enumerate(self.inbound):
                self.ib_active[idx] = (intf.valid == 1)
                self.ib_blocked += 1 if (intf.valid == 1 and intf.ready == 0) else 0
            for idx, intf in enumerate(self.outbound):
                self.ob_active[idx] = (intf.valid == 1)
                self.ob_blocked += 1 if (intf.valid == 1 and intf.ready == 0) else 0
