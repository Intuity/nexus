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

from random import choice, randint

from cocotb_bus.monitors import Monitor
from cocotb.triggers import RisingEdge, ClockCycles

class InstrRequest:
    """ Represents an instruction fetch """

    def __init__(self, address, stall, data):
        """ Initialise the request.

        Args:
            address: Address being accessed
            stall  : Number of cycles request stalled for
            data   : Response data
        """
        self.address = address
        self.stall   = stall
        self.data    = data

class InstrStore(Monitor):
    """ Testbench driven instruction store """

    def __init__(self, entity, clock, reset, intf, resp_cb=None):
        """ Initialise the instruction store.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
            resp_cb: Callback function to retrieve responses
        """
        self.entity  = entity
        self.clock   = clock
        self.reset   = reset
        self.intf    = intf
        self.resp_cb = resp_cb
        super().__init__()

    async def _monitor_recv(self):
        """ Respond to instruction fetch requests """
        while True:
            # Wait for the next clock edge
            await RisingEdge(self.clock)
            # Clear interface on reset
            if self.reset == 1:
                self.intf.data  <= 0
                self.intf.stall <= 0
                continue
            # Respond to requests
            if self.intf.rd == 1:
                address = int(self.intf.addr)
                # Randomly stall the interface
                stalled = 0
                if choice((True, False)):
                    self.intf.stall <= 1
                    stalled = randint(1, 5)
                    self.log.debug(f"Stalling instruction interface for {stalled} cycles")
                    await ClockCycles(self.clock, stalled)
                    self.intf.stall <= 0
                # Respond
                width = max(self.intf.data._range)-min(self.intf.data._range)+1
                if self.resp_cb: data = self.resp_cb(self, address)
                else           : data = randint(0, (1 << width) - 1)
                self.log.debug(f"Responding with data 0x{data:010X}")
                self.intf.data <= data
                # Capture this request
                self._recv(InstrRequest(address, stalled, data))
