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

from typing import Any, List, Optional

from drivers.stream.common import StreamTransaction
from drivers.stream.init import StreamInitiator

from nxconstants import (NodeCommand, NodeControl, NodeID, NodeLoad,
                         NodeParameter, LOAD_SEG_WIDTH, NODE_PARAM_WIDTH)
from nxmodel import NXMessagePipe, unpack_node_control, unpack_node_load

def load_data(
    inbound    : StreamInitiator,
    node_id    : NodeID,
    ram_data_w : int,
    stream     : List[Any],
    model      : Optional[NXMessagePipe] = None,
) -> None:
    """
    Load a stream of data into a node, supports either a stream of integer data
    or 'packable' types such as those from Packtype.

    Args:
        inbound   : Handle to the driver to load the node
        node_id   : Identifier for the target node
        ram_data_w: Width of the RAM in the device
        stream    : Entries to load into the device
        model     : Inbound message pipe to the model
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
            # Queue up into the testbench driver
            encoded = msg.pack()
            inbound.append(StreamTransaction(data=encoded))
            # Queue up into the C++ model if required
            if model: model.enqueue(unpack_node_load(encoded))

def load_loopback(
    inbound    : StreamInitiator,
    node_id    : NodeID,
    num_inputs : int,
    mask       : int,
    model      : Optional[NXMessagePipe] = None,
) -> None:
    """
    Load a loopback mask into a node.

    Args:
        inbound   : Handle to the driver to load the node
        node_id   : Identifier for the target node
        num_inputs: Number of inputs supported by the node
        mask      : Loopback mask
        model     : Inbound message pipe to the model
    """
    for select in range(num_inputs // NODE_PARAM_WIDTH, -1, -1):
        msg = NodeControl()
        msg.header.row     = node_id.row
        msg.header.column  = node_id.column
        msg.header.command = NodeCommand.CONTROL
        msg.param          = NodeParameter.LOOPBACK
        msg.value          = (
            (mask >> (select * NODE_PARAM_WIDTH)) & ((1 << NODE_PARAM_WIDTH) - 1)
        )
        # Queue up into the testbench driver
        encoded = msg.pack()
        inbound.append(StreamTransaction(data=encoded))
        # Queue up into the C++ model if required
        if model: model.enqueue(unpack_node_control(encoded))

def load_parameter(
    inbound   : StreamInitiator,
    node_id   : NodeID,
    parameter : NodeParameter,
    value     : int,
    model     : Optional[NXMessagePipe] = None,
) -> NodeControl:
    """
    Load a parameter into a node

    Args:
        inbound  : Handle to the driver to load the node
        node_id  : Identifier for the target node
        parameter: Parameter to configure
        value    : Value to set
        model    : Inbound message pipe to the model

    Returns: The NodeControl message for submission to monitors/scoreboarding
    """
    msg = NodeControl()
    msg.header.row     = node_id.row
    msg.header.column  = node_id.column
    msg.header.command = NodeCommand.CONTROL
    msg.param          = parameter
    msg.value          = value
    # Queue up into the testbench driver
    encoded = msg.pack()
    inbound.append(StreamTransaction(data=encoded))
    # Queue up into the C++ model if required
    if model: model.enqueue(unpack_node_control(encoded))
    # Return message for scoreboarding
    return msg
