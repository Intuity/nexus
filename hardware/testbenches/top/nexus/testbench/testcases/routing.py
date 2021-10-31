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

from nxconstants import NodeMessage

from ..testbench import testcase

@testcase()
async def routing(dut):
    """ Exercise message routing through a node """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Find the number of rows
    num_rows = int(dut.dut.dut.ROWS)
    num_cols = int(dut.dut.dut.COLUMNS)

    for _ in range(1000):
        # Keep randomising until it becomes a legal message
        msg = NodeMessage()
        while True:
            try:
                msg.unpack(randint(0, (1 << 31) - 1))
                break
            except Exception:
                continue

        # Set target outside of the fabric
        msg.raw.header.row    = num_rows
        msg.raw.header.column = randint(0, num_cols-1)

        # Create a message
        dut.debug(
            f"MSG - R: {msg.raw.header.row}, C: {msg.raw.header.column}, "
            f"CMD: {msg.raw.header.command} -> 0x{msg.pack():08X}"
        )

        # Queue up the message
        dut.mesh_inbound.append(msg.pack())
        dut.mesh_expected.append((msg.pack(), 0))
