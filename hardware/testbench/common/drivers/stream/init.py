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

class StreamInitiator(Driver):
    """ Testbench driver acting as an initiator of a stream interface """

    def __init__(self, entity, clock, reset, intf):
        """ Initialise the StreamInitiator instance.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
        """
        self.entity  = entity
        self.clock   = clock
        self.reset   = reset
        self.intf    = intf
        super().__init__()

    async def _driver_send(self, transaction, sync=True, **kwargs):
        """ Send queued transactions onto the interface.

        Args:
            transaction: Transaction to send
            sync       : Align to the rising clock edge before sending
            **kwargs   : Any other arguments
        """
        # Synchronise to the rising edge
        if sync: await RisingEdge(self.clock)
        # Wait for reset to clear
        while self.reset == 1: await RisingEdge(self.clock)
        # Drive the transaction interface
        self.intf.data  <= transaction
        self.intf.valid <= 1
        while True:
            await RisingEdge(self.clock)
            if self.intf.ready == 1: break
        self.intf.valid <= 0
