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

    # Interface and selector sizes
    MESSAGE_WIDTH    : Constant("Width of the message stream" ) = 28
    ADDR_ROW_WIDTH   : Constant("Width of the row address"    ) = ceil(log2(MAX_ROW_COUNT))
    ADDR_COL_WIDTH   : Constant("Width of the column address" ) = ceil(log2(MAX_COLUMN_COUNT))
    MAX_INPUT_WIDTH  : Constant("Width of input selector"     ) = ceil(log2(MAX_NODE_INPUTS))
    MAX_OUTPUT_WIDTH : Constant("Width of output selector"    ) = ceil(log2(MAX_NODE_OUTPUTS))
    MAX_IOR_WIDTH    : Constant("Width of in/out/reg selector") = ceil(log2(MAX_NODE_IOR_COUNT))

    # Different command type widths (control plane versus nodes in mesh)
    CTRL_CMD_WIDTH : Constant("Control message command width") = 3
    NODE_CMD_WIDTH : Constant("Node message command width"   ) = 2

    # Truth table
    TT_WIDTH : Constant("Width of a three input truth table") = 8

    # Node memory and loading
    LOAD_SEG_WIDTH      : Constant("Segment width for accumulated load") = 16
    NODE_MEM_ADDR_WIDTH : Constant("Width of node memory address"      ) = ceil(log2(MAX_NODE_MEMORY))

    # Node control
    NODE_PARAM_WIDTH : Constant("Maximum width of a node parameter") = 16

    # Trace
    TRACE_SECTION_WIDTH : Constant("Bits carried per trace message"     ) = 16
    TRACE_SELECT_WIDTH  : Constant("Width of the trace section selector") = ceil(log2(MAX_NODE_OUTPUTS / TRACE_SECTION_WIDTH))

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

@packtype.enum(package=NXConstants, mode=Enum.INDEXED)
class ControlCommand:
    """ Different message types for the control plane """
    ID       : Constant("Read the hardware identifier")
    VERSION  : Constant("Read the major and minor hardware revision")
    PARAM    : Constant("Read back different parameters")
    ACTIVE   : Constant("Set the active status of the device")
    STATUS   : Constant("Read the current status of the device")
    CYCLES   : Constant("Read the current cycle counter")
    INTERVAL : Constant("Set the number of cycles to run for")
    RESET    : Constant("Write a 1 to trigger a soft reset")

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

@packtype.enum(package=NXConstants, mode=Enum.INDEXED)
class ControlParam:
    COUNTER_WIDTH  : Constant(desc="Width of counters in the control block")
    ROWS           : Constant(desc="Number of rows in the mesh")
    COLUMNS        : Constant(desc="Number of columns in the mesh")
    NODE_INPUTS    : Constant(desc="Number of inputs per node")
    NODE_OUTPUTS   : Constant(desc="Number of outputs per node")
    NODE_REGISTERS : Constant(desc="Number of internal registers per node")

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
# Control Plane Message Formats
# ==============================================================================

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class ControlRaw:
    """ Raw payload message format for the control plane """
    command : ControlCommand(desc="Command to perform")
    payload : Scalar(width=(NXConstants.MESSAGE_WIDTH.value - ControlCommand._pt_width), desc="Payload")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class ControlReadParam:
    """ Request a parameter to be read back from the hardware """
    command : ControlCommand(desc="Command to perform")
    param   : ControlParam(desc="Parameter to query")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class ControlSetActive:
    """ Set the active state of Nexus """
    command : ControlCommand(desc="Command to perform")
    active  : Scalar(width=1, desc="Active state")

@packtype.union(package=NXConstants)
class ControlMessage:
    """ Union of different control message types """
    raw    : ControlRaw(desc="Raw message encoding")
    param  : ControlReadParam(desc="Read back parameter encoding")
    active : ControlSetActive(desc="Set active state encoding")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value)
class ControlStatus:
    """ Status response from the control plane """
    interval_set : Scalar(width=1, desc="Interval counter is set")
    first_tick   : Scalar(width=1, desc="First tick pending")
    idle_low     : Scalar(width=1, desc="Mesh idle has been seen low")
    active       : Scalar(width=1, desc="Controller is generating ticks")

@packtype.union(package=NXConstants)
class ControlResponse:
    """ Response to a control message """
    raw    : Scalar(width=NXConstants.MESSAGE_WIDTH, desc="Raw response")
    status : ControlStatus(desc="Encoded status response")

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
