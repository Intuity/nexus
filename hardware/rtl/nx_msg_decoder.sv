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

`include "nx_common.svh"

// nx_msg_decoder
// Decode messages, route commands to control blocks, and distribute messages
// marked with broadcast
//
module nx_msg_decoder
import NXConstants::*;
(
      input  logic clk_i
    , input  logic rst_i
    // Control signals
    , output logic idle_o
    // Inbound message stream
    , input  node_message_t msg_data_i
    , input  logic          msg_valid_i
    , output logic          msg_ready_o
    // I/O mapping handling
    , output logic [     IOR_WIDTH-1:0] map_idx_o     // Output to configure
    , output logic [ADDR_ROW_WIDTH-1:0] map_tgt_row_o // Target node's row
    , output logic [ADDR_COL_WIDTH-1:0] map_tgt_col_o // Target node's column
    , output logic [     IOR_WIDTH-1:0] map_tgt_idx_o // Target node's I/O index
    , output logic                      map_tgt_seq_o // Target node's input is sequential
    , output logic                      map_valid_o   // Mapping is valid
    // Signal state update
    , output logic [IOR_WIDTH-1:0] signal_index_o  // Input index
    , output logic                 signal_is_seq_o // Input is sequential
    , output logic                 signal_state_o  // Signal state
    , output logic                 signal_valid_o  // Update is valid
    // Instruction load
    , output instruction_t instr_data_o  // Instruction data
    , output logic         instr_valid_o // Instruction valid
);

// Internal signals
logic fifo_pop;

// Construct outputs
assign idle_o = (
    fifo_empty && !msg_valid_i && !map_valid_o && !signal_valid_o &&
    !instr_valid_o
);

// Inbound FIFO - buffer incoming messages ready for digestion
logic          fifo_empty, fifo_full;
node_message_t fifo_data;

nx_fifo #(
      .DEPTH(            4)
    , .WIDTH(MESSAGE_WIDTH)
) msg_fifo (
      .clk_i    (clk_i)
    , .rst_i    (rst_i)
    // Write interface
    , .wr_data_i(msg_data_i                )
    , .wr_push_i(msg_valid_i && msg_ready_o)
    // Read interface
    , .rd_data_o(fifo_data)
    , .rd_pop_i (fifo_pop )
    // Status
    , .level_o(          )
    , .empty_o(fifo_empty)
    , .full_o (fifo_full )
);

assign msg_ready_o = ~fifo_full;

// Decode the next message
node_message_t message;
assign message = fifo_data;

// - Extract output mapping from payload
`DECLARE_DQ(IOR_WIDTH,      map_idx,     clk_i, rst_i, {     IOR_WIDTH{1'b0}})
`DECLARE_DQ(ADDR_ROW_WIDTH, map_tgt_row, clk_i, rst_i, {ADDR_ROW_WIDTH{1'b0}})
`DECLARE_DQ(ADDR_COL_WIDTH, map_tgt_col, clk_i, rst_i, {ADDR_COL_WIDTH{1'b0}})
`DECLARE_DQ(IOR_WIDTH,      map_tgt_idx, clk_i, rst_i, {     IOR_WIDTH{1'b0}})
`DECLARE_DQ(1,              map_tgt_seq, clk_i, rst_i,                   1'b0)
`DECLARE_DQ(1,              map_valid,   clk_i, rst_i,                   1'b0)

assign map_idx     = message.map_output.source_index;
assign map_tgt_row = message.map_output.target_row;
assign map_tgt_col = message.map_output.target_column;
assign map_tgt_idx = message.map_output.target_index;
assign map_tgt_seq = message.map_output.target_is_seq;

assign map_idx_o     = map_idx_q;
assign map_tgt_row_o = map_tgt_row_q;
assign map_tgt_col_o = map_tgt_col_q;
assign map_tgt_idx_o = map_tgt_idx_q;
assign map_tgt_seq_o = map_tgt_seq_q;
assign map_valid_o   = map_valid_q;

// - Extract signal state update from payload
`DECLARE_DQ(IOR_WIDTH, signal_index,  clk_i, rst_i, {IOR_WIDTH{1'b0}})
`DECLARE_DQ(1,         signal_is_seq, clk_i, rst_i,              1'b0)
`DECLARE_DQ(1,         signal_state,  clk_i, rst_i,              1'b0)
`DECLARE_DQ(1,         signal_valid,  clk_i, rst_i,              1'b0)

assign signal_index  = message.sig_state.index;
assign signal_is_seq = message.sig_state.is_seq;
assign signal_state  = message.sig_state.state;

assign signal_index_o  = signal_index_q;
assign signal_is_seq_o = signal_is_seq_q;
assign signal_state_o  = signal_state_q;
assign signal_valid_o  = signal_valid_q;

// - Extract instruction load from payload
`DECLARE_DQT(instruction_t, instr_data,  clk_i, rst_i, {$bits(instruction_t){1'b0}})
`DECLARE_DQ (            1, instr_valid, clk_i, rst_i,                         1'b0)

assign instr_data = message.load_instr.instr;

assign instr_data_o  = instr_data_q;
assign instr_valid_o = instr_valid_q;

// Decode and routing
always_comb begin : p_decode
    // Initialise state
    `INIT_D(map_valid);
    `INIT_D(signal_valid);
    `INIT_D(instr_valid);

    // Always clear interface valids (no backpressure on these interfaces)
    map_valid    = 1'b0;
    signal_valid = 1'b0;
    instr_valid  = 1'b0;
    fifo_pop     = 1'b0;

    // Decode the next entry in the FIFO
    if (!fifo_empty) begin
        // Set the right decoded operation valid
        instr_valid  = (message.raw.header.command == NODE_COMMAND_LOAD_INSTR);
        map_valid    = (message.raw.header.command == NODE_COMMAND_MAP_OUTPUT);
        signal_valid = (message.raw.header.command == NODE_COMMAND_SIG_STATE );
        // Pop the FIFO as the data has been picked up
        fifo_pop = 1'b1;
    end
end

endmodule : nx_msg_decoder
