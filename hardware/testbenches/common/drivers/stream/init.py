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

from cocotb.triggers import RisingEdge

from forastero import BaseDriver
from .common import StreamTransaction

class StreamInitiator(BaseDriver):
    """ Initiator of Nexus stream interfaces """

    async def _driver_send(self, transaction, sync=True, **kwargs):
        """ Send queued transactions onto the interface.

        Args:
            transaction: Transaction to send
            sync       : Align to the rising clock edge before sending
            **kwargs   : Any other arguments
        """
        # Lock
        self.lock()
        # Check transaction type
        assert isinstance(transaction, StreamTransaction), f"Bad transaction: {transaction}"
        # Synchronise to the rising edge
        if sync: await RisingEdge(self.clock)
        # Wait for reset to clear
        while self.reset == 1: await RisingEdge(self.clock)
        # Setup the interface
        self.sniff(transaction)
        self.intf.set("data",  transaction.data)
        self.intf.set("last",  [0, 1][transaction.last])
        self.intf.set("valid", 1)
        # Drive the transaction interface
        while True:
            await RisingEdge(self.clock)
            if self.intf.ready == 1: break
        # Clear the valid
        self.intf.set("valid", 0)
        # Release lock
        self.release()
