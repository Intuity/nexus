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

from random import randint

from cocotb_bus.monitors import Monitor
from cocotb.triggers import RisingEdge, ClockCycles

from .common import AXI4StreamTransaction

class AXI4StreamResponder(Monitor):
    """ Testbench driver acting as a responder to a AXI4-Stream interface """

    def __init__(
        self, entity, clock, reset, intf, delays=True, name="AXI4StreamResponder",
        probability=0.5,
    ):
        """ Initialise the AXI4StreamResponder instance.

        Args:
            entity     : Pointer to the testbench/DUT
            clock      : Clock signal for the interface
            reset      : Reset signal for the interface
            intf       : Interface
            delays     : Enable randomised backpressure (defaults to True)
            name       : Optional name of the driver (defaults to StreamResponder)
            probability: Probability of delay
        """
        self.name        = name
        self.entity      = entity
        self.clock       = clock
        self.reset       = reset
        self.intf        = intf
        self.delays      = delays
        self.probability = probability
        super().__init__()

    async def _monitor_recv(self):
        """ Capture stream events and randomise the ready signal """
        # Work out the interface width
        data_width = self.intf.width("tdata")
        num_bytes  = data_width // 8
        # Capture buffer
        capture = None
        # Continuously monitor for transactions
        while True:
            # Wait for the next clock edge
            await RisingEdge(self.clock)
            # Clear interface on reset
            if self.reset == 1:
                self.intf.tready <= 1
                continue
            # Capture a request
            if self.intf.tvalid == 1 and self.intf.tready == 1:
                if not capture: capture = bytearray()
                tstrb   = self.intf.get("tstrb", default=((1 << num_bytes) - 1))
                tkeep   = int(self.intf.tkeep) if self.intf.has("tkeep") else tstrb
                str_val = self.intf.tdata.value._str
                for lane in range(num_bytes):
                    if ((tstrb >> lane) & 0x1) != 0 and ((tkeep >> lane) & 0x1) != 0:
                        byte = str_val[(num_bytes-lane-1)*8:(num_bytes-lane-1)*8+8]
                        capture.append(int(byte, 2))
                if self.intf.tlast == 1:
                    self._recv(AXI4StreamTransaction(
                        data  =capture,
                        id    =self.intf.get("tid",     0),
                        dest  =self.intf.get("tdest",   0),
                        user  =self.intf.get("tuser",   0),
                        wakeup=self.intf.get("twakeup", 0),
                    ))
                    capture = None
            # Generate random backpressure
            if self.delays and randint(0, 99) < int(100 * self.probability):
                self.intf.tready <= 0
                await ClockCycles(self.clock, randint(1, 10))
                self.intf.tready <= 1
