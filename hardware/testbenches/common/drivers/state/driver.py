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

from cocotb_bus.drivers import Driver
from cocotb.triggers import RisingEdge

from ..driver_common import BaseDriver

class StateInitiator(BaseDriver):
    """ Drivers signal state updates as an initiator """

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
        # Drive the request
        self.intf.index  <= transaction.index
        self.intf.is_seq <= transaction.sequential
        self.intf.value  <= transaction.state
        self.intf.update <= 1
        await RisingEdge(self.clock)
        self.intf.update <= 0
