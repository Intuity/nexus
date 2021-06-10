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

from collections import namedtuple

from cocotb_bus.monitors import Monitor
from cocotb.triggers import RisingEdge

from drivers.io_common import BaseIO

class IOMapIO(BaseIO):
    """ Input/output mapping interface from decoder """

    def __init__(self, dut, name, role):
        """ Initialise InstrLoadIO.

        Args:
            dut : Pointer to the DUT boundary
            name: Name of the signal - acts as a prefix
            role: Role of this signal on the DUT boundary
        """
        super().__init__(dut, name, role, [
            "io", "input", "remote_row", "remote_col", "remote_idx", "slot",
            "broadcast", "seq", "valid",
        ], [])

IOMapping = namedtuple("IOMapping", [
    "index", "is_input", "remote_row", "remote_col", "remote_idx", "slot",
    "broadcast", "seq"
])

class IOMapMon(Monitor):
    """ Monitors I/O mapping requests from the decoder """

    def __init__(self, entity, clock, reset, intf):
        """ Initialise the IOMapMon instance.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
        """
        self.name   = "IOMapMon"
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
                    index     =int(self.intf.io),
                    is_input  =int(self.intf.input),
                    remote_row=int(self.intf.remote_row),
                    remote_col=int(self.intf.remote_col),
                    remote_idx=int(self.intf.remote_idx),
                    slot      =int(self.intf.slot),
                    broadcast =int(self.intf.broadcast),
                    seq       =int(self.intf.seq),
                ))
