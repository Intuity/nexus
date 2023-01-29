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
from cocotb.triggers import ClockCycles, Lock, RisingEdge

class BaseDriver(Driver):

    def __init__(
        self, entity, clock, reset, intf, name=None,
    ):
        """ Initialise the BaseDriver instance.

        Args:
            entity: Pointer to the testbench/DUT
            clock : Clock signal for the interface
            reset : Reset signal for the interface
            intf  : Interface
            name  : Optional name of the driver (defaults to class name)
        """
        self.name   = name if name else type(self).__name__
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
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

    async def idle(self):
        while True:
            await RisingEdge(self.clock)
            await self.lock.acquire()
            active = len(self._sendQ) > 0 or self.busy
            self.lock.release()
            if not active: break
