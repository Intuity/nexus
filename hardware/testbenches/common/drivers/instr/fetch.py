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

from dataclasses import dataclass
from random import choice, randint

import cocotb
from cocotb_bus.drivers import Driver
from cocotb_bus.monitors import Monitor
from cocotb.triggers import RisingEdge, ClockCycles

@dataclass
class InstrFetch:
    """ Represents an instruction fetch request and response """
    address : int = 0 # Address being accessed
    stall   : int = 0 # Number of cycles request stalled for
    data    : int = 0 # Response data

class InstrFetchInitiator(Driver):
    """ Drives requests on the instruction fetch bus """

    def __init__(self, entity, clock, reset, intf):
        """ Initialise the instruction fetch initiator.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
        """
        self.name   = "InstrFetchInitiator"
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
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
        # Drive the request
        self.intf.addr <= transaction.address
        self.intf.rd   <= 1
        await RisingEdge(self.clock)
        transaction.stall = 0
        while self.intf.stall == 1:
            transaction.stall += 1
            await RisingEdge(self.clock)
        self.intf.rd <= 0
        # Launch a coroutine to pickup the response on the next cycle
        async def pickup_data():
            await RisingEdge(self.clock)
            transaction.data = int(self.intf.data)
        cocotb.fork(pickup_data())

class InstrFetchResponder(Monitor):
    """ Testbench driven instruction store """

    def __init__(self, entity, clock, reset, intf, resp_cb=None):
        """ Initialise the instruction fetch responder.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
            resp_cb: Callback function to retrieve responses
        """
        self.name    = "InstrFetchResponder"
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
                self._recv(InstrFetch(address, stalled, data))
