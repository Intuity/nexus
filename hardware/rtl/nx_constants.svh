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

// Interface sizes
`define NX_MESSAGE_WIDTH     32 // Width of a message stream interface
`define NX_DIRECTION_WIDTH    2 // Width of the message direction interface
`define NX_INSTRUCTION_WIDTH 15 // Width an instruction
`define NX_INPUT_WIDTH        3 // Width of input index
`define NX_OUTPUT_WIDTH       3 // Width of output index

// Header Fields
`define NX_ROW_ADDR_WIDTH    4 // Row address width
`define NX_COLUMN_ADDR_WIDTH 4 // Column address width
`define NX_COMMAND_WIDTH     2 // Command encoding width

// Instruction Fields
`define NX_INSTR_OPCODE_WIDTH 3 // Instruction encoded operation
`define NX_INSTR_SOURCE_WIDTH 3 // Operation source width
`define NX_INSTR_TARGET_WIDTH 3 // Operation target width

typedef enum logic [`NX_DIRECTION_WIDTH-1:0] {
    NX_DIRX_NORTH, // 0 - Arriving from/sending to the north
    NX_DIRX_EAST,  // 1 - ...the east
    NX_DIRX_SOUTH, // 2 - ...the south
    NX_DIRX_WEST   // 3 - ...the west
} nx_direction_t;

typedef enum logic [`NX_COMMAND_WIDTH-1:0] {
    NX_CMD_LOAD_INSTR, // 0: Instruction load
    NX_CMD_MAP_OUTPUT, // 1: Output mapping
    NX_CMD_SIG_STATE,  // 2: Signal state update
    NX_CMD_NODE_CTRL   // 3: Node control
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
} nx_message_t;

typedef struct packed {
    nx_msg_header_t  header;
    nx_instruction_t instruction;
    logic [
        $bits(nx_message_t)     -
        $bits(nx_msg_header_t)  -
        $bits(nx_instruction_t) -
        1:0
    ] _padding;
} nx_msg_load_instr_t;

typedef struct packed {
    nx_msg_header_t                   header;
    logic [     `NX_OUTPUT_WIDTH-1:0] source_index;
    logic [   `NX_ROW_ADDR_WIDTH-1:0] target_row;
    logic [`NX_COLUMN_ADDR_WIDTH-1:0] target_column;
    logic [      `NX_INPUT_WIDTH-1:0] target_index;
    logic                             target_is_seq;
    logic [
        $bits(nx_message_t)    -
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
        $bits(nx_message_t)    -
        $bits(nx_msg_header_t) -
        `NX_INPUT_WIDTH        -
        1                      - // Sequential flag
        1                      - // State
        1:0
    ] _padding;
} nx_msg_sig_state_t;

`endif // __NX_CONSTANTS_SVH__
