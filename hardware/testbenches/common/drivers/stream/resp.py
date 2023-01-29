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

from cocotb.triggers import RisingEdge
from cocotb.utils import get_sim_time

from forastero import BaseMonitor
from .common import StreamTransaction

class StreamResponder(BaseMonitor):
    """ Testbench driver acting as a responder to a stream interface """

    async def _monitor_recv(self):
        """ Capture stream events and randomise the ready signal """
        # Wait for a cycle
        await RisingEdge(self.clock)
        # Loop forever
        while True:
            # Wait for the next clock edge
            if self.reset == 1:
                self.intf.set("ready", 1)
                await RisingEdge(self.clock)
                continue
            # Capture a request
            if self.intf.get("valid") and self.intf.get("ready", 1):
                self._recv(StreamTransaction(
                    timestamp=get_sim_time(units="ns"),
                    data     =int(self.intf.data),
                    last     =(self.intf.get("last", 0) == 1),
                ))
            # Wait for the next cycle
            await RisingEdge(self.clock)
