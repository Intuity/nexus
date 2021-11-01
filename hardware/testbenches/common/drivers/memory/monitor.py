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
from cocotb.triggers import RisingEdge

from .common import MemoryTransaction

class MemoryMonitor(Monitor):
    """ Testbench driver acting as a responder to a memory interface """

    def __init__(
        self, entity, clock, reset, intf, name="MemoryMonitor",
    ):
        """ Initialise the MemoryMonitor instance.

        Args:
            entity     : Pointer to the testbench/DUT
            clock      : Clock signal for the interface
            reset      : Reset signal for the interface
            intf       : Interface
            name       : Optional name of the monitor (defaults to MemoryMonitor)
            probability: Probability of delay
        """
        self.name   = name
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
        super().__init__()

    async def _monitor_recv(self):
        """ Capture requests to the memory """
        # Wait for a cycle
        await RisingEdge(self.clock)
        # Loop forever
        while True:
            # Skip transactions when under reset
            if self.reset == 1:
                await RisingEdge(self.clock)
                continue
            # Detect active read or write transactions
            if self.intf.get("rd_en") or self.intf.get("wr_en"):
                # Capture request
                tran = MemoryTransaction(
                    addr   =self.intf.get("addr",    0),
                    wr_data=self.intf.get("wr_data", 0),
                    wr_en  =self.intf.get("wr_en",   0),
                    rd_en  =self.intf.get("rd_en",   0)
                )
                # Wait at least one cycle
                while True:
                    await RisingEdge(self.clock)
                    if not self.intf.get("stall"): break
                # Capture read data
                tran.rd_data = self.intf.get("rd_data", 0)
                # Store the transaction
                self._recv(tran)
            # Otherwise wait for the next cycle
            else:
                await RisingEdge(self.clock)
