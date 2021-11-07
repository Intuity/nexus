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

from typing import List

from drivers.stream.common import StreamTransaction
from drivers.stream.init import StreamInitiator

from nxconstants import NodeCommand, NodeID, NodeSignal

async def update_inputs(
    inbound       : StreamInitiator,
    node_id       : NodeID,
    previous      : List[bool],
    updated       : List[bool],
    is_seq        : List[bool],
    only_seq      : bool = False,
    only_com      : bool = False,
    only_changed  : bool = True,
    wait_for_idle : bool = True,
) -> None:
    """
    Update the input state of a node, generating and submitting messages to an
    inbound queue.

    Args:
        inbound      : Driver to send messages into the node
        node_id      : Identifier of the target node
        previous     : Previous state of inputs
        updated      : New state of inputs
        is_seq       : Map of which inputs are sequential vs combinatorial
        only_seq     : Only send sequential updates
        only_com     : Only send combinatorial updates
        only_changed : Only send updates where a state has changed
        wait_for_idle: Whether to wait for the driver to return to idle
    """
    # Queue up all of the messages
    for index, (prev, new, seq) in enumerate(zip(previous, updated, is_seq)):
        # Suppress updates where signal has not changed
        if only_changed and (prev == new): continue
        # Suppress combinatorial updates
        if only_seq and not seq: continue
        # Suppress sequential updates
        if only_com and seq: continue
        # Otherwise generate a message
        msg = NodeSignal()
        msg.header.row     = node_id.row
        msg.header.column  = node_id.column
        msg.header.command = NodeCommand.SIGNAL
        msg.index          = index
        msg.is_seq         = (1 if seq else 0)
        msg.state          = (1 if new else 0)
        inbound.append(StreamTransaction(data=msg.pack()))
    # Wait for driver to return to idle
    if wait_for_idle: await inbound.idle()
