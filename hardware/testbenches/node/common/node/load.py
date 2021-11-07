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

from typing import Any, List

from drivers.stream.common import StreamTransaction
from drivers.stream.init import StreamInitiator

from nxconstants import (NodeCommand, NodeControl, NodeID, NodeLoad,
                         NodeLoopback, NodeParameter, LOAD_SEG_WIDTH,
                         LB_SECTION_WIDTH)

def load_data(
    inbound    : StreamInitiator,
    node_id    : NodeID,
    ram_data_w : int,
    stream     : List[Any],
) -> None:
    """
    Load a stream of data into a node, supports either a stream of integer data
    or 'packable' types such as those from Packtype.

    Args:
        inbound   : Handle to the driver to load the node
        node_id   : Identifier for the target node
        ram_data_w: Width of the RAM in the device
        stream    : Entries to load into the device
    """
    chunks = ram_data_w // LOAD_SEG_WIDTH
    mask   = (1 << LOAD_SEG_WIDTH) - 1
    for entry in stream:
        data = entry if isinstance(entry, int) else entry.pack()
        for chunk in range(ram_data_w // LOAD_SEG_WIDTH):
            msg = NodeLoad()
            msg.header.row     = node_id.row
            msg.header.column  = node_id.column
            msg.header.command = NodeCommand.LOAD
            msg.last           = (chunk == (chunks - 1))
            msg.data           = (
                (data >> ((chunks - chunk - 1) * LOAD_SEG_WIDTH)) & mask
            )
            inbound.append(StreamTransaction(data=msg.pack()))

def load_loopback(
    inbound    : StreamInitiator,
    node_id    : NodeID,
    num_inputs : int,
    mask       : int
) -> None:
    """
    Load a loopback mask into a node.

    Args:
        inbound   : Handle to the driver to load the node
        node_id   : Identifier for the target node
        num_inputs: Number of inputs supported by the node
        mask      : Loopback mask
    """
    for select in range(num_inputs // LB_SECTION_WIDTH):
        msg = NodeLoopback()
        msg.header.row     = node_id.row
        msg.header.column  = node_id.column
        msg.header.command = NodeCommand.LOOPBACK
        msg.select         = select
        msg.section        = (
            (mask >> (select * LB_SECTION_WIDTH)) & ((1 << LB_SECTION_WIDTH) - 1)
        )
        inbound.append(StreamTransaction(data=msg.pack()))

def load_parameter(
    inbound   : StreamInitiator,
    node_id   : NodeID,
    parameter : NodeParameter,
    value     : int,
) -> NodeControl:
    """
    Load a parameter into a node

    Args:
        inbound  : Handle to the driver to load the node
        node_id  : Identifier for the target node
        parameter: Parameter to configure
        value    : Value to set

    Returns: The NodeControl message for submission to monitors/scoreboarding
    """
    msg = NodeControl()
    msg.header.row     = node_id.row
    msg.header.column  = node_id.column
    msg.header.command = NodeCommand.CONTROL
    msg.param          = parameter
    msg.value          = value
    inbound.append(StreamTransaction(data=msg.pack()))
    return msg
