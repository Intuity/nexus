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

from math import ceil, log2

import packtype
from packtype import Constant, Enum, Scalar, Struct

def clog2(obj):
    if isinstance(obj, Constant):
        return int(ceil(log2(obj.value))) if obj.value > 0 else 1
    else:
        return int(ceil(log2(obj))) if obj > 0 else 1

# ==============================================================================
# Package Declaration
# ==============================================================================

@packtype.package()
class NXConstants:
    """ Constants and types related to Nexus """
    # Device identifiers
    HW_DEV_ID    : Constant("Hardware identifier"    ) = 0x4E5853 # NXS in ASCII
    HW_VER_MAJOR : Constant("Major hardware revision") = 0
    HW_VER_MINOR : Constant("Minor hardware revision") = 3

    # Maximum sizes
    MAX_ROW_COUNT      : Constant("Maximum number of rows"              ) = 16
    MAX_COLUMN_COUNT   : Constant("Maximum number of columns"           ) = 16
    MAX_NODE_MEMORY    : Constant("Maximum 16-bit memory rows per node" ) = 2048
    MAX_NODE_REGISTERS : Constant("Maximum number of registers per node") = 8
    MAX_MESH_OUTPUTS   : Constant("Maximum outputs of the mesh"         ) = MAX_COLUMN_COUNT * 32

    # Control plane constants
    CONTROL_WIDTH     : Constant("Width of the control stream" ) = 128
    HOST_PACKET_SIZE  : Constant("Maximum to-host packet size" ) = 4096
    SLOTS_PER_PACKET  : Constant("Control responses per packet") = (HOST_PACKET_SIZE * 8) // CONTROL_WIDTH
    TIMER_WIDTH       : Constant("Width of the control timers" ) = 24
    OUT_BITS_PER_MSG  : Constant("Bits of output per message"  ) = 96
    MAX_OUT_IDX_WIDTH : Constant("Output index field width"    ) = clog2(MAX_MESH_OUTPUTS / OUT_BITS_PER_MSG)

    # Top-level memory constants
    TOP_MEM_COUNT      : Constant("Number of on-board memories"  ) = 2
    TOP_MEM_IDX_WIDTH  : Constant("On-board memory index width"  ) = clog2(TOP_MEM_COUNT)
    TOP_MEM_ADDR_WIDTH : Constant("On-board memory address width") = 10
    TOP_MEM_DATA_WIDTH : Constant("On-board memory data width"   ) = 32
    TOP_MEM_STRB_WIDTH : Constant("On-board memory write strobe" ) = TOP_MEM_DATA_WIDTH // 8

    # Interface and selector sizes
    MESSAGE_WIDTH : Constant("Width of the message stream") = 31
    ID_ROW_WIDTH  : Constant("Width of the row address"   ) = clog2(MAX_ROW_COUNT)
    ID_COL_WIDTH  : Constant("Width of the column address") = clog2(MAX_COLUMN_COUNT)

    # Truth table
    TT_WIDTH : Constant("Width of a three input truth table") = 8

    # Node memory and loading
    NODE_MEM_ADDR_WIDTH      : Constant("Address width for node memory") = clog2(MAX_NODE_MEMORY)
    NODE_MEM_SLOT_WIDTH      : Constant("Width of a memory slot"       ) = 8
    NODE_MEM_SLOT_MODE_WIDTH : Constant("Width of the slot mode"       ) = 2
    NODE_MEM_SLOT_SEL_WIDTH  : Constant("Width of the slot selector"   ) = 1

# ==============================================================================
# Enumerations
# ==============================================================================

@packtype.enum(package=NXConstants, mode=Enum.INDEXED)
class Direction:
    """ Enumerates directions for send and receive """
    NORTH : Constant("Sending to/arriving from the north")
    EAST  : Constant("Sending to/arriving from the east" )
    SOUTH : Constant("Sending to/arriving from the south")
    WEST  : Constant("Sending to/arriving from the west" )

@packtype.enum(package=NXConstants)
class ControlReqType:
    """ Control request type enumeration """
    READ_PARAMS : Constant("Read back the device's parameters" )
    READ_STATUS : Constant("Read back the device's status"     )
    SOFT_RESET  : Constant("Request a soft reset"              )
    CONFIGURE   : Constant("Configure the controller"          )
    TRIGGER     : Constant("Trigger the device to run"         )
    TO_MESH     : Constant("Forward message into the mesh"     )
    MEMORY      : Constant("Read and write the on-board memory")

@packtype.enum(package=NXConstants)
class ControlRespType:
    """ Control response type enumeration """
    OUTPUTS   : Constant("Reporting the current outputs"     )
    FROM_MESH : Constant("Message forwarded from the mesh"   )
    PARAMS    : Constant("Device parameters"                 )
    STATUS    : Constant("Status of the controller and mesh" )
    PADDING   : Constant("Packetised response padding marker")
    MEMORY    : Constant("Data read from the on-board memory")

@packtype.enum(package=NXConstants, mode=Enum.INDEXED)
class NodeCommand:
    """ Different message types for nodes in the mesh """
    LOAD   : Constant("Load data into the node's memory")
    SIGNAL : Constant("Carries signal state to and from a node")

@packtype.enum(package=NXConstants, mode=Enum.INDEXED, width=NXConstants.NODE_MEM_SLOT_MODE_WIDTH.value)
class MemorySlot:
    """ Memory slot modes """
    PRESERVE : Constant("Use the node's current state"               )
    INVERSE  : Constant("Use the inverse of the node's current state")
    LOWER    : Constant("Explicitly use the lower slot"              )
    UPPER    : Constant("Explicitly use the upper slot"              )

# ==============================================================================
# Node Identifier
# ==============================================================================

@packtype.struct(package=NXConstants)
class NodeID:
    """ Identifier for a node """
    row    : Scalar(width=NXConstants.ID_ROW_WIDTH, desc="Row within the mesh"   )
    column : Scalar(width=NXConstants.ID_COL_WIDTH, desc="Column within the mesh")

# ==============================================================================
# Node Message Formats
# ==============================================================================

@packtype.struct(package=NXConstants, width=10, pack=Struct.FROM_MSB)
class NodeHeader:
    """ Header for messages directed to nodes in the mesh """
    target  : NodeID(desc="Target node in the mesh")
    command : NodeCommand(desc="Encoded command")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeRaw:
    """ Raw payload message format for nodes in the mesh """
    header  : NodeHeader(desc="Header carrying row, column, and command")
    payload : Scalar(width=(NXConstants.MESSAGE_WIDTH.value - NodeHeader._pt_width), desc="Payload")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeLoad:
    """ Load data into a node's instruction memory """
    header  : NodeHeader(desc="Header carrying row, column, and command")
    address : Scalar(width=NXConstants.NODE_MEM_ADDR_WIDTH, desc="Row to write into")
    slot    : Scalar(width=NXConstants.NODE_MEM_SLOT_SEL_WIDTH, desc="Slot selection")
    data    : Scalar(width=NXConstants.NODE_MEM_SLOT_WIDTH,
                     desc ="Data to write into memory")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeSignal:
    """ Write into a node's data memory """
    header  : NodeHeader(desc="Header carrying row, column, and command")
    address : Scalar(width=NXConstants.NODE_MEM_ADDR_WIDTH, desc="Row to write into")
    slot    : MemorySlot(desc="Slot mode")
    data    : Scalar(width=NXConstants.NODE_MEM_SLOT_WIDTH,
                     desc ="Data to write into memory")

@packtype.union(package=NXConstants)
class NodeMessage:
    """ Union of different node message types """
    raw    : NodeRaw(desc="Raw message encoding")
    load   : NodeLoad(desc="Data load encoding")
    signal : NodeSignal(desc="Signal state encoding")

# ==============================================================================
# Control Plane Message Formats
# ==============================================================================

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlRequestRaw:
    """ Control request with command and raw payload """
    command : ControlReqType(desc="Command to perform")
    payload : Scalar(width=(NXConstants.CONTROL_WIDTH.value - ControlReqType._pt_width), desc="Payload")

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlRequestConfigure:
    """ Configure the controller """
    command      : ControlReqType(desc="Command to perform")
    en_memory    : Scalar(width=NXConstants.TOP_MEM_COUNT.value, desc="Enable/disable on-board memory"      )
    en_mem_wstrb : Scalar(width=NXConstants.TOP_MEM_COUNT.value, desc="Enable/disable memory write strobing")
    output_mask  : Scalar(
        width=(1 << NXConstants.MAX_OUT_IDX_WIDTH.value),
        desc="Mask of which output messages should be emitted"
    )

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlRequestTrigger:
    """ Control request to trigger the mesh """
    command  : ControlReqType(desc="Command to perform")
    col_mask : Scalar(width=NXConstants.MAX_COLUMN_COUNT.value, desc="Columns to trigger")
    cycles   : Scalar(width=NXConstants.TIMER_WIDTH.value,      desc="Cycles to run for" )
    active   : Scalar(width=1,                                  desc="Enable/disable"    )

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlRequestToMesh:
    """ Control request to forward message into the mesh """
    command : ControlReqType(desc="Command to perform")
    message : Scalar(width=NXConstants.MESSAGE_WIDTH.value, desc="Message to forward into the mesh")

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlRequestMemory:
    """ Request read and write operations from the on-board memory """
    command : ControlReqType(desc="Command to perform")
    memory  : Scalar(width=NXConstants.TOP_MEM_IDX_WIDTH.value,  desc="Memory index")
    address : Scalar(width=NXConstants.TOP_MEM_ADDR_WIDTH.value, desc="Access address")
    wr_n_rd : Scalar(width=1, desc="Set high to write, low to read")
    wr_data : Scalar(width=NXConstants.TOP_MEM_DATA_WIDTH.value, desc="Write data")
    wr_strb : Scalar(width=NXConstants.TOP_MEM_STRB_WIDTH.value, desc="Write strobe")

@packtype.union(package=NXConstants)
class ControlRequest:
    """ Control requests sent by the host """
    raw       : ControlRequestRaw(desc="Raw control format")
    configure : ControlRequestConfigure(desc="Configure the controller")
    trigger   : ControlRequestTrigger(desc="Trigger control format")
    to_mesh   : ControlRequestToMesh(desc="Forward message into mesh format")
    memory    : ControlRequestMemory(desc="Access on-board memory")

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponseRaw:
    """ Raw control response format """
    format  : ControlRespType(desc="Control response format")
    payload : Scalar(width=NXConstants.CONTROL_WIDTH.value - ControlRespType._pt_width)

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponseParameters:
    """ Parameters of the device """
    format      : ControlRespType(desc="Control response format")
    id          : Scalar(width=clog2(NXConstants.HW_DEV_ID)+1,          desc="Hardware identifier")
    ver_major   : Scalar(width=clog2(NXConstants.HW_VER_MAJOR)+1,       desc="Major version"      )
    ver_minor   : Scalar(width=clog2(NXConstants.HW_VER_MINOR)+1,       desc="Minor version"      )
    timer_width : Scalar(width=clog2(NXConstants.TIMER_WIDTH)+1,        desc="Timer width"        )
    rows        : Scalar(width=clog2(NXConstants.MAX_ROW_COUNT)+1,      desc="Number of rows"     )
    columns     : Scalar(width=clog2(NXConstants.MAX_COLUMN_COUNT)+1,   desc="Number of columns"  )
    node_regs   : Scalar(width=clog2(NXConstants.MAX_NODE_REGISTERS)+1, desc="Registers per node" )

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponseStatus:
    """ Status of the device """
    format     : ControlRespType(desc="Control response format")
    active     : Scalar(width=1, desc="If the controller is active")
    mesh_idle  : Scalar(width=1, desc="Is the mesh idle?")
    agg_idle   : Scalar(width=1, desc="Are the aggregators idle?")
    seen_low   : Scalar(width=1, desc="Has the idle signal been seen low?")
    first_tick : Scalar(width=1, desc="Is this the first tick after reset?")
    cycle      : Scalar(width=NXConstants.TIMER_WIDTH.value, desc="Current cycle")
    countdown  : Scalar(width=NXConstants.TIMER_WIDTH.value, desc="Remaining cycles")

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponseOutputs:
    """ Control response carrying sections of the output vector """
    format  : ControlRespType(desc="Control response format")
    stamp   : Scalar(width=NXConstants.TIMER_WIDTH.value, desc="Simulation cycle")
    index   : Scalar(width=clog2(NXConstants.MAX_MESH_OUTPUTS.value / 96),
                     desc ="Which section of the full outputs is included")
    section : Scalar(width=96, desc="Section of the outputs")

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponseFromMesh:
    """ Forwarded message from the mesh """
    format  : ControlRespType(desc="Control response format")
    message : Scalar(width=NXConstants.MESSAGE_WIDTH.value, desc="Forwarded message")

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponseMemory:
    """ Read response from the on-board memory """
    format  : ControlRespType(desc="Control response format")
    rd_data : Scalar(width=NXConstants.TOP_MEM_DATA_WIDTH.value, desc="Read data")

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponsePadding:
    """ Padding used to signify unused entries following this response """
    format  : ControlRespType(desc="Control response format")
    entries : Scalar(
        width=clog2(NXConstants.SLOTS_PER_PACKET),
        desc="Number of padding entries"
    )

@packtype.union(package=NXConstants)
class ControlResponse:
    """ Control responses sent by the device """
    raw       : ControlResponseRaw(desc="Raw response format")
    params    : ControlResponseParameters(desc="Parameters of the device")
    status    : ControlResponseStatus(desc="Status of the device")
    outputs   : ControlResponseOutputs(desc="Reports the current outputs")
    from_mesh : ControlResponseFromMesh(desc="Forwards messages from the mesh")
    memory    : ControlResponseMemory(desc="Read response from on-board memory")
    padding   : ControlResponsePadding(desc="Padding message format")
