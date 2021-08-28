// Copyright 2021, Peter Birch, mailto:peter@lightlogic.co.uk
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

`ifndef __NX_CONSTANTS_SVH__
`define __NX_CONSTANTS_SVH__

// =============================================================================
// Constants
// =============================================================================

// NOTE: Message width is set to 31 as the MSB is used to route either into the
//       control block or into the mesh

// Maximum mesh size
`define NX_MAX_ROW_COUNT      16
`define NX_MAX_COLUMN_COUNT   16

// Interface sizes
`define NX_MESSAGE_WIDTH      31 // Width of a message stream interface
`define NX_INPUT_WIDTH        5  // Width of input index
`define NX_OUTPUT_WIDTH       5  // Width of output index

// Header Fields
`define NX_ROW_ADDR_WIDTH     $clog2(`NX_MAX_ROW_COUNT   )
`define NX_COLUMN_ADDR_WIDTH  $clog2(`NX_MAX_COLUMN_COUNT)
`define NX_COMMAND_WIDTH      2 // Command encoding width
`define NX_CTRL_CMD_WIDTH     3 // Control block command width
`define NX_CTRL_PARAM_WIDTH   3 // Parameter selection width

// Instruction Fields
`define NX_INSTR_OPCODE_WIDTH 3 // Encoded operation width
`define NX_INSTR_SOURCE_WIDTH 5 // Operation source index width
`define NX_INSTR_TARGET_WIDTH 5 // Operation target index width

// Identifiers
`define NX_DEVICE_ID          24'h4E5853 // NXS in ASCII
`define NX_VERSION_MAJOR      8'd0
`define NX_VERSION_MINOR      8'd3

// =============================================================================
// Mesh Enumerations
// =============================================================================

typedef enum logic [1:0] {
      NX_DIRX_NORTH // 0 - Arriving from/sending to the north
    , NX_DIRX_EAST  // 1 - ...the east
    , NX_DIRX_SOUTH // 2 - ...the south
    , NX_DIRX_WEST  // 3 - ...the west
} nx_direction_t;

// =============================================================================
// Messages Enumerations and Structures for Nodes in Mesh
// =============================================================================

typedef enum logic [`NX_COMMAND_WIDTH-1:0] {
      NX_CMD_LOAD_INSTR // 0: Instruction load
    , NX_CMD_MAP_OUTPUT // 1: Output mapping
    , NX_CMD_SIG_STATE  // 2: Signal state update
    , NX_CMD_NODE_CTRL  // 3: Node control
} nx_command_t;

typedef enum logic [`NX_INSTR_OPCODE_WIDTH-1:0] {
      NX_OP_INVERT // 0 - !A
    , NX_OP_AND    // 1 -   A & B
    , NX_OP_NAND   // 2 - !(A & B)
    , NX_OP_OR     // 3 -   A | B
    , NX_OP_NOR    // 4 - !(A | B)
    , NX_OP_XOR    // 5 -   A ^ B
    , NX_OP_XNOR   // 6 - !(A ^ B)
    , NX_OP_UNUSED // 7 - Unassigned
} nx_instruction_op_t;

typedef struct packed {
    nx_instruction_op_t                opcode;   // Encoded operation
    logic [`NX_INSTR_SOURCE_WIDTH-1:0] src_a;    // Source index A
    logic                              src_a_ip; // Is source A from inputs?
    logic [`NX_INSTR_SOURCE_WIDTH-1:0] src_b;    // Source index B
    logic                              src_b_ip; // Is source B from inputs?
    logic [`NX_INSTR_TARGET_WIDTH-1:0] tgt_reg;  // Target register
    logic                              gen_out;  // Generates output flag
} nx_instruction_t;

typedef struct packed {
    logic [   `NX_ROW_ADDR_WIDTH-1:0] row;
    logic [`NX_COLUMN_ADDR_WIDTH-1:0] column;
    nx_command_t                      command;
} nx_msg_header_t;

typedef struct packed {
    nx_msg_header_t                                      header;
    logic [`NX_MESSAGE_WIDTH-$bits(nx_msg_header_t)-1:0] payload;
} nx_msg_raw_t;

typedef struct packed {
    nx_msg_header_t  header;
    nx_instruction_t instruction;
} nx_msg_load_instr_t;

typedef struct packed {
    nx_msg_header_t                   header;
    logic [     `NX_OUTPUT_WIDTH-1:0] source_index;
    logic [   `NX_ROW_ADDR_WIDTH-1:0] target_row;
    logic [`NX_COLUMN_ADDR_WIDTH-1:0] target_column;
    logic [      `NX_INPUT_WIDTH-1:0] target_index;
    logic                             target_is_seq;
    logic [
        `NX_MESSAGE_WIDTH      -
        $bits(nx_msg_header_t) -
        `NX_OUTPUT_WIDTH       -
        `NX_ROW_ADDR_WIDTH     -
        `NX_COLUMN_ADDR_WIDTH  -
        `NX_INPUT_WIDTH        -
        1                      - // Sequential flag
        1:0
    ] _padding;
} nx_msg_map_output_t;

typedef struct packed {
    nx_msg_header_t             header;
    logic [`NX_INPUT_WIDTH-1:0] target_index;
    logic                       target_is_seq;
    logic                       state;
    logic [
        `NX_MESSAGE_WIDTH      -
        $bits(nx_msg_header_t) -
        `NX_INPUT_WIDTH        -
        1                      - // Sequential flag
        1                      - // State
        1:0
    ] _padding;
} nx_msg_sig_state_t;

typedef union packed {
    nx_msg_raw_t        raw;
    nx_msg_load_instr_t load_instr;
    nx_msg_map_output_t map_output;
    nx_msg_sig_state_t  sig_state;
} nx_message_t;

// =============================================================================
// Messages Enumerations and Structures for Control Plane
// =============================================================================

typedef enum logic [`NX_CTRL_CMD_WIDTH-1:0] {
      NX_CTRL_ID       // 0: Read device identifier
    , NX_CTRL_VERSION  // 1: Read hardware version (major/minor)
    , NX_CTRL_PARAM    // 2: Read back different parameters
    , NX_CTRL_ACTIVE   // 3: Set the active status of the device
    , NX_CTRL_STATUS   // 4: Read back the current status
    , NX_CTRL_CYCLES   // 5: Read current cycle counter
    , NX_CTRL_INTERVAL // 6: Set number of cycles to run for
    , NX_CTRL_RESET    // 7: Write 1 to trigger a soft reset of Nexus
} nx_ctrl_command_t;

typedef enum logic [`NX_CTRL_PARAM_WIDTH-1:0] {
      NX_PARAM_COUNTER_WIDTH  // 0: Width of counters in the control block
    , NX_PARAM_ROWS           // 1: Number of rows in the mesh
    , NX_PARAM_COLUMNS        // 2: Number of columns in the mesh
    , NX_PARAM_NODE_INPUTS    // 3: Number of inputs per node
    , NX_PARAM_NODE_OUTPUTS   // 4: Number of outputs per node
    , NX_PARAM_NODE_REGISTERS // 5: Number of internal registers per node
} nx_ctrl_param_t;

typedef struct packed {
    nx_ctrl_command_t command;
    logic [
        `NX_MESSAGE_WIDTH        - // Total message width
        $bits(nx_ctrl_command_t) - // Control command
        1:0
    ] payload;
} nx_ctrl_msg_raw_t;

typedef struct packed {
    nx_ctrl_command_t command;
    nx_ctrl_param_t   param;
    logic [
        `NX_MESSAGE_WIDTH        - // Total message width
        $bits(nx_ctrl_command_t) - // Control command
        $bits(nx_ctrl_param_t)   - // Parameter selection
        1:0
    ] _padding;
} nx_ctrl_msg_param_t;

typedef struct packed {
    nx_ctrl_command_t command;
    logic             active;
    logic [
        `NX_MESSAGE_WIDTH        - // Total message width
        $bits(nx_ctrl_command_t) - // Control command
        1                        - // Active field
        1:0
    ] _padding;
} nx_ctrl_msg_active_t;

typedef struct packed {
    nx_ctrl_command_t command;
    logic [
        `NX_MESSAGE_WIDTH        - // Total message width
        $bits(nx_ctrl_command_t) - // Control command
        1:0
    ] interval;
} nx_ctrl_msg_interval_t;

typedef union packed {
    nx_ctrl_msg_raw_t      raw;
    nx_ctrl_msg_param_t    param;
    nx_ctrl_msg_active_t   active;
    nx_ctrl_msg_interval_t interval;
} nx_ctrl_msg_t;

typedef struct packed {
    logic [`NX_MESSAGE_WIDTH-1:0] payload;
} nx_ctrl_msg_resp_t;

`endif // __NX_CONSTANTS_SVH__
