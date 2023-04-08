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
from nxconstants import NodeRaw, MAX_ROW_COUNT, MAX_COLUMN_COUNT, MESSAGE_WIDTH

from ..testbench import Testbench

@Testbench.testcase()
async def routing(tb):
    """ Exercise message routing through a node """
    # Select an inbound interface
    inbound = choice(tb.all_inbound)

    # Queue up many packets
    for idx in range(1000):
        # Generate a random message
        msg = NodeRaw()
        msg.unpack(randint(0, (1 << MESSAGE_WIDTH) - 1))

        # Select a different target row and column
        while True:
            msg.header.target.row    = randint(0, MAX_ROW_COUNT-1)
            msg.header.target.column = randint(0, MAX_COLUMN_COUNT-1)
            if (msg.header.target.row, msg.header.target.column) != (tb.node_id.row, tb.node_id.column):
                break

        # Queue up the inbound message
        inbound.append(StreamTransaction(sequence=idx, data=msg.pack()))
