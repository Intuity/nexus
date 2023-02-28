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

from cocotb.triggers import ClockCycles

from ..testbench import Testbench

@Testbench.testcase()
async def sanity(tb):
    """ Basic testcase """
    # Run for 100 clock cycles
    tb.info("Running for 100 clock cycles")
    await ClockCycles(tb.clk, 100)

    # All done!
    tb.info("Finished counting cycles")