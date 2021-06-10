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

class StateIO(BaseIO):
    """ Signal state interface from decoder """

    def __init__(self, dut, name, role):
        """ Initialise InstrLoadIO.

        Args:
            dut : Pointer to the DUT boundary
            name: Name of the signal - acts as a prefix
            role: Role of this signal on the DUT boundary
        """
        super().__init__(dut, name, role, [
            "remote_row", "remote_col", "remote_idx", "state", "valid",
        ], [])

SignalState = namedtuple("SignalState", [
    "remote_row", "remote_col", "remote_idx", "state"
])

class StateMon(Monitor):
    """ Monitors signal state updates from the decoder """

    def __init__(self, entity, clock, reset, intf):
        """ Initialise the InstrMon instance.

        Args:
            entity : Pointer to the testbench/DUT
            clock  : Clock signal for the interface
            reset  : Reset signal for the interface
            intf   : Interface
        """
        self.name   = "InstrMon"
        self.entity = entity
        self.clock  = clock
        self.reset  = reset
        self.intf   = intf
        super().__init__()

    async def _monitor_recv(self):
        """ Capture signal states being updated """
        while True:
            # Wait for the next clock edge
            await RisingEdge(self.clock)
            # Skip cycle if reset
            if self.reset == 1: continue
            # Capture any I/O mappings
            if self.intf.valid == 1:
                self._recv(SignalState(
                    remote_row=int(self.intf.remote_row),
                    remote_col=int(self.intf.remote_col),
                    remote_idx=int(self.intf.remote_idx),
                    state     =int(self.intf.state),
                ))
