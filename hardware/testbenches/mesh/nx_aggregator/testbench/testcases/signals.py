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

from random import choice, randint

from drivers.stream.common import StreamTransaction
from nxconstants import (NodeCommand, NodeID, NodeRaw, NodeSignal, MAX_ROW_COUNT,
                         MAX_COLUMN_COUNT, MESSAGE_WIDTH, MAX_NODE_OUTPUTS)

from ..testbench import testcase

@testcase()
async def signals(dut):
    """ Exercise output aggregation of signal messages """
    # Reset the DUT
    dut.info("Resetting the DUT")
    await dut.reset()

    # Decide on a row and column
    node_id = NodeID(
        row   =randint(0, MAX_ROW_COUNT-1   ),
        column=randint(0, MAX_COLUMN_COUNT-1),
    )
    dut.node_id <= node_id.pack()

    # Queue up many signal updates
    state = 0
    for _ in range(1000):
        # 50% of the time send a signal message
        if choice((True, False)):
            msg = NodeSignal()
            msg.header.row     = randint(0, MAX_ROW_COUNT-1)
            msg.header.column  = node_id.column
            msg.header.command = NodeCommand.SIGNAL
            msg.index          = randint(0, MAX_NODE_OUTPUTS - 1)
            msg.is_seq         = choice((0, 1))
            msg.state          = choice((0, 1))
            # Track state
            if msg.state:
                new_state = state | (1 << msg.index)
            else:
                new_state = state & (((1 << MAX_NODE_OUTPUTS) - 1) - (1 << msg.index))
            if new_state != state:
                dut.exp_output.append(new_state)
            state = new_state
        # Otherwise send a random message (not using SIGNAL command)
        else:
            msg = NodeRaw()
            msg.unpack(randint(0, (1 << MESSAGE_WIDTH) - 1))
            msg.header.command = choice((
                NodeCommand.LOAD, NodeCommand.CONTROL, NodeCommand.TRACE
            ))
            dut.exp_stream.append(StreamTransaction(data=msg.pack()))
        # Queue onto the inbound driver
        dut.inbound.append(StreamTransaction(data=msg.pack()))
        # Sporadically inject a passthrough message
        if choice((True, False)):
            msg = randint(0, (1 << MESSAGE_WIDTH) - 1)
            dut.passthrough.append(StreamTransaction(data=msg))
            dut.exp_stream.append(StreamTransaction(data=msg))
