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

from .common import IOMapping

class IOMapMonitor(Monitor):
    """ Monitors I/O mapping requests from the decoder """

    def __init__(self, entity, clock, reset, intf):
        """ Initialise the IOMapMonitor instance.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
        """
        self.name   = "IOMapMonitor"
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
        super().__init__()

    async def _monitor_recv(self):
        """ Capture inputs/outputs being mapped """
        while True:
            # Wait for the next clock edge
            await RisingEdge(self.clock)
            # Skip cycle if reset
            if self.reset == 1: continue
            # Capture any I/O mappings
            if self.intf.valid == 1:
                self._recv(IOMapping(
                    index     =int(self.intf.idx),
                    target_row=int(self.intf.tgt_row),
                    target_col=int(self.intf.tgt_col),
                    target_idx=int(self.intf.tgt_idx),
                    target_seq=int(self.intf.tgt_seq),
                ))
