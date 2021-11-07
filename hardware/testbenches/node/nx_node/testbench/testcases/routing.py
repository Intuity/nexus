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

from random import choice, randint

from drivers.stream.common import StreamTransaction
from nxconstants import (Direction, NodeID, NodeRaw, MAX_ROW_COUNT,
                         MAX_COLUMN_COUNT, MESSAGE_WIDTH)

from ..testbench import testcase

@testcase()
async def routing(dut):
    """ Exercise message routing through a node """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Decide on a row and column
    node_id = NodeID(
        row   =randint(0, MAX_ROW_COUNT-1   ),
        column=randint(0, MAX_COLUMN_COUNT-1),
    )
    dut.node_id <= node_id.pack()

    # Select an inbound interface
    inbound = choice(dut.inbound)

    # Queue up many packets
    for _ in range(1000):
        # Generate a random message
        msg = NodeRaw()
        msg.unpack(randint(0, (1 << MESSAGE_WIDTH) - 1))

        # Select a different target row and column
        while True:
            msg.header.row    = randint(0, MAX_ROW_COUNT-1)
            msg.header.column = randint(0, MAX_COLUMN_COUNT-1)
            if (msg.header.row, msg.header.column) != (node_id.row, node_id.column):
                break

        # Queue up the inbound message
        inbound.append(StreamTransaction(data=msg.pack()))

        # Queue up the message onto the right outbound queue
        if msg.header.row < node_id.row:
            dut.expected[int(Direction.NORTH)].append(StreamTransaction(data=msg.pack()))
        elif msg.header.row > node_id.row:
            dut.expected[int(Direction.SOUTH)].append(StreamTransaction(data=msg.pack()))
        elif msg.header.column < node_id.column:
            dut.expected[int(Direction.WEST)].append(StreamTransaction(data=msg.pack()))
        elif msg.header.column > node_id.column:
            dut.expected[int(Direction.EAST)].append(StreamTransaction(data=msg.pack()))
        else:
            raise Exception("Could not route message")
