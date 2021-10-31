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
from cocotb_bus.drivers import Driver
from cocotb.triggers import RisingEdge

from .common import MemoryTransaction

class MemoryInitiator(Driver):
    """ Testbench driver acting as an initiator to a memory interface """

    def __init__(
        self, entity, clock, reset, intf, name="MemoryInitiator",
    ):
        """ Initialise the MemoryInitiator instance.

        Args:
            entity     : Pointer to the testbench/DUT
            clock      : Clock signal for the interface
            reset      : Reset signal for the interface
            intf       : Interface
            name       : Optional name of the driver (defaults to MemoryInitiator)
            probability: Probability of delay
        """
        self.name   = name
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
        Driver.__init__(self)

    async def _driver_send(self, transaction, sync=True, **kwargs):
        """ Send queued transactions onto the interface.

        Args:
            transaction: Transaction to send
            sync       : Align to the rising clock edge before sending
            **kwargs   : Any other arguments
        """
        # Synchronise if required
        if sync: await RisingEdge(self.clock)
        # Wait for reset to clear
        while self.reset == 1: await RisingEdge(self.clock)
        # Setup the interface
        self.intf.addr    <= transaction.addr
        self.intf.wr_data <= transaction.wr_data
        self.intf.wr_en   <= (1 if transaction.wr_en else 0)
        self.intf.rd_en   <= (1 if transaction.rd_en else 0)
        # Wait for one cycle
        await RisingEdge(self.clock)
        # Clear write/read enable
        self.intf.wr_en <= 0
        self.intf.rd_en <= 0
        # Launch coroutine to pickup response
        async def pickup_resp():
            await RisingEdge(self.clock)
            transaction.rd_data = int(self.intf.rd_data)
        cocotb.fork(pickup_resp())
