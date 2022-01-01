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
from cocotb.triggers import Lock, RisingEdge, ClockCycles

from .common import StreamTransaction

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
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
        self.busy   = False
        self.lock   = Lock()
        super().__init__()

    async def _send_thread(self):
        while True:
            # Sleep until there is something to send
            while not self._sendQ:
                self._pending.clear()
                await self._pending.wait()
            # Always start out-of-sync
            synchronised = False
            # Send in all queued packets
            await self.lock.acquire()
            self.busy = True
            self.lock.release()
            while self._sendQ:
                tran, cb, evt, kwargs = self._sendQ.popleft()
                self.log.debug("Sending queued packet")
                try:
                    await self._send(tran, cb, evt, sync=not synchronised, **kwargs)
                except ValueError as e:
                    self.log.error(f"Hit value error: {e}")
                    await ClockCycles(self.clock, 10)
                    raise e
                synchronised = True
            await self.lock.acquire()
            self.busy = False
            self.lock.release()

    async def _driver_send(self, transaction, sync=True, **kwargs):
        """ Send queued transactions onto the interface.

        Args:
            transaction: Transaction to send
            sync       : Align to the rising clock edge before sending
            **kwargs   : Any other arguments
        """
        # Check transaction type
        assert type(transaction) in (int, StreamTransaction), \
            f"Unsupported transaction type {type(transaction).__name__}"
        # Sanitise
        if isinstance(transaction, int):
            transaction = StreamTransaction(data=transaction)
        # Synchronise to the rising edge
        if sync: await RisingEdge(self.clock)
        # Wait for reset to clear
        while self.reset == 1: await RisingEdge(self.clock)
        # Drive the transaction interface
        self.intf.data <= transaction.data
        self.intf.set("last", 1 if transaction.last else 0)
        self.intf.set("dir", int(transaction.direction))
        self.intf.valid <= 1
        while True:
            await RisingEdge(self.clock)
            if self.intf.ready == 1: break
        self.intf.valid <= 0

    async def idle(self):
        while True:
            await RisingEdge(self.clock)
            await self.lock.acquire()
            active = len(self._sendQ) > 0 or self.busy
            self.lock.release()
            if not active: break
