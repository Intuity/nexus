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
    MAX_ROW_COUNT      : Constant("Maximum number of rows"                ) = 16
    MAX_COLUMN_COUNT   : Constant("Maximum number of columns"             ) = 16
    MAX_NODE_MEMORY    : Constant("Maximum memory rows per node"          ) = 1024
    MAX_NODE_INPUTS    : Constant("Maximum number of inputs per node"     ) = 32
    MAX_NODE_OUTPUTS   : Constant("Maximum number of outputs per node"    ) = 32
    MAX_NODE_REGISTERS : Constant("Maximum number of registers per node"  ) = 32
    MAX_NODE_IOR_COUNT : Constant("Max input, output, or register count"  ) = max(
        MAX_NODE_INPUTS, MAX_NODE_OUTPUTS, MAX_NODE_REGISTERS
    )
    MAX_MESH_OUTPUTS   : Constant("Maximum outputs of the mesh"           ) = (
        MAX_COLUMN_COUNT * MAX_NODE_OUTPUTS
    )

    # Interface and selector sizes
    CONTROL_WIDTH     : Constant("Width of the control stream" ) = 128
    MESSAGE_WIDTH     : Constant("Width of the message stream" ) = 28
    ADDR_ROW_WIDTH    : Constant("Width of the row address"    ) = clog2(MAX_ROW_COUNT)
    ADDR_COL_WIDTH    : Constant("Width of the column address" ) = clog2(MAX_COLUMN_COUNT)
    MAX_INPUT_WIDTH   : Constant("Width of input selector"     ) = clog2(MAX_NODE_INPUTS)
    MAX_OUTPUT_WIDTH  : Constant("Width of output selector"    ) = clog2(MAX_NODE_OUTPUTS)
    MAX_IOR_WIDTH     : Constant("Width of in/out/reg selector") = clog2(MAX_NODE_IOR_COUNT)
    TIMER_WIDTH       : Constant("Width of the control timers" ) = 24
    OUT_BITS_PER_MSG  : Constant("Bits of output per message"  ) = 96
    MAX_OUT_IDX_WIDTH : Constant("Output index field width"    ) = clog2(
        (MAX_COLUMN_COUNT * MAX_NODE_OUTPUTS) / OUT_BITS_PER_MSG
    )

    # Truth table
    TT_WIDTH : Constant("Width of a three input truth table") = 8

    # Node memory and loading
    LOAD_SEG_WIDTH      : Constant("Segment width for accumulated load") = 16
    NODE_MEM_ADDR_WIDTH : Constant("Width of node memory address"      ) = clog2(MAX_NODE_MEMORY)

    # Node control
    NODE_PARAM_WIDTH : Constant("Maximum width of a node parameter") = 16

    # Trace
    TRACE_SECTION_WIDTH : Constant("Bits carried per trace message"     ) = 16
    TRACE_SELECT_WIDTH  : Constant("Width of the trace section selector") = clog2(MAX_NODE_OUTPUTS / TRACE_SECTION_WIDTH)

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
    READ_PARAMS : Constant("Read back the device's parameters")
    READ_STATUS : Constant("Read back the device's status"    )
    SOFT_RESET  : Constant("Request a soft reset"             )
    TRIGGER     : Constant("Trigger the device to run"        )
    TO_MESH     : Constant("Forward message into the mesh"    )

@packtype.enum(package=NXConstants)
class ControlRespType:
    """ Control response type enumeration """
    OUTPUTS   : Constant("Reporting the current outputs"    )
    FROM_MESH : Constant("Message forwarded from the mesh"  )
    PARAMS    : Constant("Device parameters"                )
    STATUS    : Constant("Status of the controller and mesh")

@packtype.enum(package=NXConstants, mode=Enum.INDEXED)
class NodeCommand:
    """ Different message types for nodes in the mesh """
    LOAD    : Constant("Load data into the node's memory")
    SIGNAL  : Constant("Carries signal state to and from a node")
    CONTROL : Constant("Set parameters for the node")
    TRACE   : Constant("Trace from the output state of a node")

@packtype.enum(package=NXConstants, mode=Enum.INDEXED)
class NodeParameter:
    """ Different control parameters within the node """
    INSTRUCTIONS : Constant("Number of instructions")
    LOOPBACK     : Constant("Loopback mask (existing value shifted up by 16 on write)")
    TRACE        : Constant("Trace output values on every cycle")

@packtype.enum(package=NXConstants, mode=Enum.INDEXED)
class Operation:
    """ Operation encoding for instructions """
    INVERT   : Constant("X = !(A    )")
    AND      : Constant("X =  (A & B)")
    NAND     : Constant("X = !(A & B)")
    OR       : Constant("X =  (A | B)")
    NOR      : Constant("X = !(A | B)")
    XOR      : Constant("X =  (A ^ B)")
    XNOR     : Constant("X = !(A ^ B)")
    RESERVED : Constant("Reserved instruction")

# ==============================================================================
# Node Identifier
# ==============================================================================

@packtype.struct(package=NXConstants)
class NodeID:
    """ Identifier for a node """
    row    : Scalar(width=NXConstants.ADDR_ROW_WIDTH, desc="Row within the mesh")
    column : Scalar(width=NXConstants.ADDR_COL_WIDTH, desc="Column within the mesh")

# ==============================================================================
# Instruction Format
# ==============================================================================

@packtype.struct(package=NXConstants, width=32, pack=Struct.FROM_MSB)
class Instruction:
    """ Node instruction encoding """
    truth    : Scalar(width=NXConstants.TT_WIDTH, desc="Encoded truth table")
    src_a    : Scalar(width=NXConstants.MAX_IOR_WIDTH, desc="Source selector A")
    src_a_ip : Scalar(width=1, desc="Primary input (1) or a register (0)")
    src_b    : Scalar(width=NXConstants.MAX_IOR_WIDTH, desc="Source selector B")
    src_b_ip : Scalar(width=1, desc="Primary input (1) or a register (0)")
    src_c    : Scalar(width=NXConstants.MAX_IOR_WIDTH, desc="Source selector C")
    src_c_ip : Scalar(width=1, desc="Primary input (1) or a register (0)")
    tgt_reg  : Scalar(width=NXConstants.MAX_IOR_WIDTH, desc="Target register")
    gen_out  : Scalar(width=1, desc="Generate an output message")

# ==============================================================================
# Output Mappings
# ==============================================================================

@packtype.struct(package=NXConstants)
class OutputLookup:
    """ Node output lookup encoding (lists start and end point of messages) """
    active : Scalar(width=1,                               desc="Is external output")
    start  : Scalar(width=NXConstants.NODE_MEM_ADDR_WIDTH, desc="Start address")
    stop   : Scalar(width=NXConstants.NODE_MEM_ADDR_WIDTH, desc="Stop address")

@packtype.struct(package=NXConstants)
class OutputMapping:
    """ Single node output mapping """
    row    : Scalar(width=NXConstants.ADDR_ROW_WIDTH, desc="Target row")
    column : Scalar(width=NXConstants.ADDR_COL_WIDTH, desc="Target column")
    index  : Scalar(width=NXConstants.MAX_IOR_WIDTH,  desc="Target index")
    is_seq : Scalar(width=1,                          desc="Is target sequential")

# ==============================================================================
# Node Message Formats
# ==============================================================================

@packtype.struct(package=NXConstants, width=10, pack=Struct.FROM_MSB)
class NodeHeader:
    """ Header for messages directed to nodes in the mesh """
    row     : Scalar(width=NXConstants.ADDR_ROW_WIDTH, desc="Row in the mesh")
    column  : Scalar(width=NXConstants.ADDR_COL_WIDTH, desc="Column in the mesh")
    command : NodeCommand(desc="Encoded command")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeRaw:
    """ Raw payload message format for nodes in the mesh """
    header  : NodeHeader(desc="Header carrying row, column, and command")
    payload : Scalar(width=(NXConstants.MESSAGE_WIDTH.value - NodeHeader._pt_width), desc="Payload")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeLoad:
    """ Load data into a node's memory in segments (accumulated on receive) """
    header : NodeHeader(desc="Header carrying row, column, and command")
    last   : Scalar(width=1,                          desc="Marks the final segment")
    data   : Scalar(width=NXConstants.LOAD_SEG_WIDTH, desc="Segment of data to load")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeSignal:
    """ Signal state carried to/from a node """
    header : NodeHeader(desc="Header carrying row, column, and command")
    index  : Scalar(width=NXConstants.MAX_IOR_WIDTH, desc="Input signal index")
    is_seq : Scalar(width=1, desc="Is the input signal sequential or combinatorial")
    state  : Scalar(width=1, desc="Value of the signal")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeControl:
    """ Set attributes of a node """
    header : NodeHeader(desc="Header carrying row, column, and command")
    param  : NodeParameter(desc="Parameter to update")
    value  : Scalar(width=NXConstants.NODE_PARAM_WIDTH, desc="Updated value")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeTrace:
    """ Trace output state of a node """
    header : NodeHeader(desc="Header carrying row, column, and command")
    select : Scalar(width=NXConstants.TRACE_SELECT_WIDTH,  desc="Trace section")
    trace  : Scalar(width=NXConstants.TRACE_SECTION_WIDTH, desc="Section value")

@packtype.union(package=NXConstants)
class NodeMessage:
    """ Union of different node message types """
    raw      : NodeRaw(desc="Raw message encoding")
    load     : NodeLoad(desc="Data load encoding")
    signal   : NodeSignal(desc="Signal state encoding")
    control  : NodeControl(desc="Parameter control encoding")
    trace    : NodeControl(desc="Output trace encoding")


# ==============================================================================
# Control Plane Message Formats
# ==============================================================================

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlRequestRaw:
    """ Control request with command and raw payload """
    command : ControlReqType(desc="Command to perform")
    payload : Scalar(width=(NXConstants.CONTROL_WIDTH.value - ControlReqType._pt_width), desc="Payload")

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

@packtype.union(package=NXConstants)
class ControlRequest:
    """ Control requests sent by the host """
    raw     : ControlRequestRaw(desc="Raw control format")
    trigger : ControlRequestTrigger(desc="Trigger control format")
    to_mesh : ControlRequestToMesh(desc="Forward message into mesh format")

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponseOutputs:
    """ Control response carrying sections of the output vector """
    format  : ControlRespType(desc="Control response format")
    stamp   : Scalar(width=NXConstants.TIMER_WIDTH.value, desc="Simulation cycle")
    index   : Scalar(width=clog2(
        (NXConstants.MAX_COLUMN_COUNT.value * NXConstants.MAX_NODE_OUTPUTS.value) / 96
    ), desc="Which section of the full outputs is included")
    section : Scalar(width=96, desc="Section of the outputs")

@packtype.struct(package=NXConstants, width=NXConstants.CONTROL_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponseFromMesh:
    """ Forwarded message from the mesh """
    format  : ControlRespType(desc="Control response format")
    message : Scalar(width=NXConstants.MESSAGE_WIDTH.value, desc="Forwarded message")

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
    node_ins    : Scalar(width=clog2(NXConstants.MAX_NODE_INPUTS)+1,    desc="Inputs per node"    )
    node_outs   : Scalar(width=clog2(NXConstants.MAX_NODE_OUTPUTS)+1,   desc="Outputs per node"   )
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

@packtype.union(package=NXConstants)
class ControlResponse:
    """ Control responses sent by the device """
    params    : ControlResponseParameters(desc="Parameters of the device")
    status    : ControlResponseStatus(desc="Status of the device")
    outputs   : ControlResponseOutputs(desc="Reports the current outputs")
    from_mesh : ControlResponseFromMesh(desc="Forwards messages from the mesh")
