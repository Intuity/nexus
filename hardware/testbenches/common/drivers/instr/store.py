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

from dataclasses import dataclass
from cocotb_bus.drivers import Driver
from cocotb_bus.monitors import Monitor
from cocotb.triggers import RisingEdge

@dataclass
class InstrStore:
    """ Represents an instruction store request """
    data : int = 0 # Instruction data

class InstrStoreInitiator(Driver):
    """ Drives requests on the instruction store bus """

    def __init__(self, entity, clock, reset, intf):
        """ Initialise the instruction store initiator.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
        """
        self.name   = "InstrStoreInitiator"
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
        self.intf.data  <= transaction.data
        self.intf.valid <= 1
        await RisingEdge(self.clock)
        self.intf.valid <= 0

class InstrStoreMonitor(Monitor):
    """ Monitors instruction load events """

    def __init__(self, entity, clock, reset, intf):
        """ Initialise the InstrStoreMon instance.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
        """
        self.name   = "InstrStoreMon"
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
        super().__init__()

    async def _monitor_recv(self):
        """ Capture instructions being loaded """
        while True:
            # Wait for the next clock edge
            await RisingEdge(self.clock)
            # Skip cycle if reset
            if self.reset == 1: continue
            # Capture any instruction loads
            if self.intf.valid == 1:
                self._recv(InstrStore(int(self.intf.data)))
