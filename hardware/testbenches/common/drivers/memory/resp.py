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

import cocotb
from cocotb_bus.drivers import Driver
from cocotb_bus.monitors import Monitor
from cocotb.triggers import ClockCycles, RisingEdge

class MemoryResponder(Driver, Monitor):
    """ Testbench driver acting as a responder to a memory interface """

    def __init__(
        self, entity, clock, reset, intf, name="MemoryResponder", delay=1,
    ):
        """ Initialise the MemoryResponder instance.

        Args:
            entity: Pointer to the testbench/DUT
            clock : Clock signal for the interface
            reset : Reset signal for the interface
            intf  : Interface
            name  : Optional name of the driver (defaults to MemoryResponder)
            delay : Cycles of delay between request and response
        """
        self.name   = name
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
        self.delay  = delay
        self.memory = {}
        Driver.__init__(self)
        Monitor.__init__(self)
        self.stats.reads      = 0
        self.stats.writes     = 0
        self.stats.last_read  = 0
        self.stats.last_write = 0

    async def _driver_send(self, transaction, sync=True, **kwargs):
        """ Send queued transactions onto the interface.

        Args:
            transaction: Transaction to send
            sync       : Align to the rising clock edge before sending
            **kwargs   : Any other arguments
        """
        # Never synchronise - already synced by monitor
        # Drive the memory response
        if self.delay > 1:
            async def delayed(tran):
                await ClockCycles(self.clock, (self.delay - 1))
                self.intf.set("rd_data", tran)
                self.intf.set("stall", 0)
            cocotb.fork(delayed(transaction))
        else:
            self.intf.set("rd_data", transaction)
            self.intf.set("stall", 0)

    async def _monitor_recv(self):
        """ Capture requests to the memory """
        while True:
            # Wait for the next clock edge
            await RisingEdge(self.clock)
            # Skip transactions when under reset
            if self.reset == 1: continue
            # Handle requests
            if self.intf.get("wr_en"):
                self.memory[int(self.intf.addr)] = self.intf.get("wr_data")
                self.stats.writes += 1
                self.stats.last_write = int(self.intf.addr)
            elif self.intf.get("rd_en"):
                self.append(self.memory.get(self.intf.get("addr"), 0))
                self.stats.reads += 1
                self.stats.last_read = int(self.intf.addr)
