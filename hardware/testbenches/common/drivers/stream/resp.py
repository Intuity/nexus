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

from random import randint

from cocotb_bus.monitors import Monitor
from cocotb.triggers import RisingEdge, ClockCycles

class StreamResponder(Monitor):
    """ Testbench driver acting as a responder to a stream interface """

    def __init__(
        self, entity, clock, reset, intf, delays=True, name="StreamResponder",
        probability=0.5,
    ):
        """ Initialise the StreamResponder instance.

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
        while True:
            # Wait for the next clock edge
            await RisingEdge(self.clock)
            # Clear interface on reset
            if self.reset == 1:
                self.intf.ready <= 1
                continue
            # Capture a request
            if self.intf.valid == 1 and self.intf.ready == 1:
                if hasattr(self.intf, "dir"):
                    self._recv((int(self.intf.data), int(self.intf.dir)))
                else:
                    self._recv((int(self.intf.data), 0))
            # Generate random backpressure
            if self.delays and randint(0, 99) < int(100 * self.probability):
                self.intf.ready <= 0
                await ClockCycles(self.clock, randint(1, 10))
                self.intf.ready <= 1
