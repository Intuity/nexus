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
    MAX_NODE_INSTRS    : Constant("Maximum instructions per node"         ) = 512
    MAX_NODE_CONFIG    : Constant("Maximum output configurations per node") = 512
    MAX_NODE_INPUTS    : Constant("Maximum number of inputs per node"     ) = 32
    MAX_NODE_OUTPUTS   : Constant("Maximum number of outputs per node"    ) = 32
    MAX_NODE_REGISTERS : Constant("Maximum number of registers per node"  ) = 32
    MAX_NODE_IOR_COUNT : Constant("Max input, output, or register count"  ) = max(
        MAX_NODE_INPUTS, MAX_NODE_OUTPUTS, MAX_NODE_REGISTERS
    )

    # Interface and selector sizes
    MESSAGE_WIDTH  : Constant("Width of the message stream" ) = 31
    ADDR_ROW_WIDTH : Constant("Width of the row address"    ) = ceil(log2(MAX_ROW_COUNT))
    ADDR_COL_WIDTH : Constant("Width of the column address" ) = ceil(log2(MAX_COLUMN_COUNT))
    INPUT_WIDTH    : Constant("Width of input selector"     ) = ceil(log2(MAX_NODE_INPUTS))
    OUTPUT_WIDTH   : Constant("Width of output selector"    ) = ceil(log2(MAX_NODE_OUTPUTS))
    IOR_WIDTH      : Constant("Width of in/out/reg selector") = ceil(log2(MAX_NODE_IOR_COUNT))

    # Different command type widths (control plane versus nodes in mesh)
    CTRL_CMD_WIDTH : Constant("Control message command width") = 3
    NODE_CMD_WIDTH : Constant("Node message command width"   ) = 2

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
    LOAD_INSTR : Constant("Load a new instruction")
    MAP_OUTPUT : Constant("Add an output signal mapping")
    SIG_STATE  : Constant("Update input signal state for a node")
    NODE_CTRL  : Constant("Control node behaviour")

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
# Instruction Format
# ==============================================================================

@packtype.struct(package=NXConstants, width=21, pack=Struct.FROM_MSB)
class Instruction:
    """ Node instruction encoding """
    opcode   : Operation(desc="Operation to perform")
    src_a    : Scalar(width=NXConstants.IOR_WIDTH, desc="Source selector A")
    src_a_ip : Scalar(width=1, desc="Primary input (1) or a register (0)")
    src_b    : Scalar(width=NXConstants.IOR_WIDTH, desc="Source selector B")
    src_b_ip : Scalar(width=1, desc="Primary input (1) or a register (0)")
    tgt_reg  : Scalar(width=NXConstants.IOR_WIDTH, desc="Target register")
    gen_out  : Scalar(width=1, desc="Generate an output message")

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

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class ControlResponse:
    """ Response to a control message """
    payload : Scalar(width=NXConstants.MESSAGE_WIDTH, desc="Response payload")

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
class NodeLoadInstr:
    """ Load an instruction into a node """
    header : NodeHeader(desc="Header carrying row, column, and command")
    instr  : Instruction(desc="Encoded instruction")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeMapOutput:
    """ Append a mapping for an output of the node """
    header        : NodeHeader(desc="Header carrying row, column, and command")
    source_index  : Scalar(width=NXConstants.IOR_WIDTH, desc="Output signal index")
    target_row    : Scalar(width=NXConstants.ADDR_ROW_WIDTH, desc="Target row in the mesh")
    target_column : Scalar(width=NXConstants.ADDR_COL_WIDTH, desc="Target column in the mesh")
    target_index  : Scalar(width=NXConstants.IOR_WIDTH.value, desc="Input index of the target node")
    target_is_seq : Scalar(width=1, desc="Is the target's input sequential")

@packtype.struct(package=NXConstants, width=NXConstants.MESSAGE_WIDTH.value, pack=Struct.FROM_MSB)
class NodeSigState:
    """ Updates input signal state of a node """
    header : NodeHeader(desc="Header carrying row, column, and command")
    index  : Scalar(width=NXConstants.IOR_WIDTH.value, desc="Input signal index")
    is_seq : Scalar(width=1, desc="Is the input signal sequential or combinatorial")
    state  : Scalar(width=1, desc="Value of the signal")

@packtype.union(package=NXConstants)
class NodeMessage:
    """ Union of different node message types """
    raw        : NodeRaw(desc="Raw message encoding")
    load_instr : NodeLoadInstr(desc="Load instruction encoding")
    map_output : NodeMapOutput(desc="Map output encoding")
    sig_state  : NodeSigState(desc="Signal state update encoding")
