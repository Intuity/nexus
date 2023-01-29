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
from cocotb.triggers import RisingEdge

from .common import MemoryTransaction
from ..driver_common import BaseDriver

class MemoryInitiator(BaseDriver):
    """ Testbench driver acting as an initiator to a memory interface """

    async def _driver_send(self, transaction, sync=True, **kwargs):
        """ Send queued transactions onto the interface.

        Args:
            transaction: Transaction to send
            sync       : Align to the rising clock edge before sending
            **kwargs   : Any other arguments
        """
        # Check transaction
        assert isinstance(transaction, MemoryTransaction), "Bad transaction type"
        # Synchronise if required
        if sync: await RisingEdge(self.clock)
        # Wait for reset to clear
        while self.reset == 1: await RisingEdge(self.clock)
        # Setup the interface
        self.intf.set("addr", transaction.addr)
        self.intf.set("wr_data", transaction.wr_data)
        self.intf.set("wr_en", (1 if transaction.wr_en else 0))
        self.intf.set("rd_en", (1 if transaction.rd_en else 0))
        # Wait for at least one cycle
        while True:
            await RisingEdge(self.clock)
            if not self.intf.get("stall"): break
        # Clear write/read enable
        self.intf.set("wr_en", 0)
        self.intf.set("rd_en", 0)
        # Launch coroutine to pickup response
        if self.intf.has("rd_data"):
            async def pickup_resp():
                await RisingEdge(self.clock)
                transaction.rd_data = int(self.intf.rd_data)
            cocotb.fork(pickup_resp())
