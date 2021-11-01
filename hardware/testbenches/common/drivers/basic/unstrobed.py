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

from cocotb_bus.monitors import Monitor
from cocotb.triggers import RisingEdge

class UnstrobedMonitor(Monitor):
    """ Collect the value of an interface every time it changes """

    def __init__(self, entity, clock, reset, intf, name=None):
        """ Initialise the UnstrobedMonitor instance.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
        """
        self.name   = name if name else type(self).__name__
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
        super().__init__()

    async def _monitor_recv(self):
        """ Capture signal states being updated """
        active     = False
        last_value = 0
        while True:
            # Wait for the next clock edge
            await RisingEdge(self.clock)
            # Clear state if reset
            if self.reset == 1:
                active     = False
                last_value = 0
            # If active, compare and snapshot on every change
            curr_value = int(self.intf)
            if active and curr_value != last_value:
                self._recv(curr_value)
            # Capture the value on every cycle
            last_value = curr_value
            # Mark as active on every cycle after the first out of reset
            active = True
