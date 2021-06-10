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

from cocotb.triggers import ClockCycles

class TestbenchBase:

    def __init__(self, dut):
        """ Initialise the base testbench.

        Args:
            dut: Pointer to the DUT
        """
        # Hold a pointer to the DUT
        self.dut = dut
        # Promote clock & reset
        self.clk = dut.clk
        self.rst = dut.rst
        # Expose logging methods
        self.debug   = dut._log.debug
        self.info    = dut._log.info
        self.warning = dut._log.warning
        self.error   = dut._log.error

    async def initialise(self):
        """ Initialise the DUT's I/O """
        self.rst <= 1

    async def reset(self, init=True, wait=20):
        """ Reset the DUT.

        Args:
            init: Initialise the DUT's I/O
            wait: Number of clock cycles to wait after init and reset
        """
        # Drive reset high
        self.rst <= 1
        # Initialise I/O
        if init:
            await self.initialise()
            await ClockCycles(self.clk, wait)
        # Drop reset
        self.rst <= 0
        # Wait for a bit
        await ClockCycles(self.clk, wait)

    def __getattr__(self, key):
        """ Pass through accesses to signals on the DUT.

        Args:
            key: Name of the attribute
        """
        try:
            return super().__getattr__(key)
        except Exception:
            return getattr(self.dut, key)
