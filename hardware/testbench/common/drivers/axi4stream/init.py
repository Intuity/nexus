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

from cocotb_bus.drivers import Driver
from cocotb.triggers import RisingEdge

from .common import AXI4StreamTransaction

class AXI4StreamInitiator(Driver):
    """ Testbench driver acting as an initiator of an AXI4-Stream interface """

    def __init__(self, entity, clock, reset, intf):
        """ Initialise the AXI4StreamInitiator instance.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
        """
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
        self.busy   = False
        super().__init__()

    async def _driver_send(self, transaction, sync=True, **kwargs):
        """ Send queued transactions onto the interface.

        Args:
            transaction: Transaction to send
            sync       : Align to the rising clock edge before sending
            **kwargs   : Any other arguments
        """
        # Lock
        self.busy = True
        # Check for the correct transaction type
        assert isinstance(transaction, AXI4StreamTransaction), \
            "Bad AXI4-Stream transaction object"
        # Synchronise to the rising edge
        if sync: await RisingEdge(self.clock)
        # Wait for reset to clear
        while self.reset == 1: await RisingEdge(self.clock)
        # Drive the transaction interface
        all_bytes  = transaction.data[:]
        data_width = self.intf.width("tdata")
        num_bytes  = data_width // 8
        for chunk, strobe in transaction.pack(num_bytes):
            # Setup compulsory fields
            self.intf.tdata  <= chunk
            self.intf.tstrb  <= strobe
            self.intf.tvalid <= 1
            self.intf.tlast  <= 0 if all_bytes else 1
            # Setup optional fields
            self.intf.set("tkeep"  , strobe)
            self.intf.set("tid"    , transaction.id)
            self.intf.set("tdest"  , transaction.dest)
            self.intf.set("tuser"  , transaction.user)
            self.intf.set("twakeup", transaction.wakeup)
            # Wait for transaction to be accepted
            while True:
                await RisingEdge(self.clock)
                if self.intf.tready == 1: break
            # Clear the valid
            self.intf.tvalid <= 0
        # Release
        self.busy = False

    async def idle(self):
        await RisingEdge(self.clock)
        if not self._sendQ and not self.busy: return
        while self._sendQ or self.busy: await RisingEdge(self.clock)
