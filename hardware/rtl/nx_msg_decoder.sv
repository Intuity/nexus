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
`include "nx_constants.svh"

// nx_msg_decoder
// Decode messages, route commands to control blocks, and distribute messages
// marked with broadcast
//
module nx_msg_decoder #(
      parameter STREAM_WIDTH   = 32 // Width of the stream interface
    , parameter ADDR_ROW_WIDTH =  4 // Message row address field width
    , parameter ADDR_COL_WIDTH =  4 // Message column address field width
    , parameter COMMAND_WIDTH  =  2 // Message command field width
    , parameter INSTR_WIDTH    = 15 // Width of each instruction
    , parameter INPUTS         =  8 // Number of inputs
    , parameter OUTPUTS        =  8 // Number of outputs
) (
      input  logic clk_i
    , input  logic rst_i
    // Control signals
    , output logic idle_o
    // Inbound message stream
    , input  nx_message_t msg_data_i
    , input  logic        msg_valid_i
    , output logic        msg_ready_o
    // I/O mapping handling
    , output logic [$clog2(OUTPUTS)-1:0] map_idx_o     // Output to configure
    , output logic [ ADDR_ROW_WIDTH-1:0] map_tgt_row_o // Target node's row
    , output logic [ ADDR_COL_WIDTH-1:0] map_tgt_col_o // Target node's column
    , output logic [ $clog2(INPUTS)-1:0] map_tgt_idx_o // Target node's I/O index
    , output logic                       map_tgt_seq_o // Target node's input is sequential
    , output logic                       map_valid_o   // Mapping is valid
    // Signal state update
    , output logic [$clog2(INPUTS)-1:0] signal_index_o  // Input index
    , output logic                      signal_is_seq_o // Input is sequential
    , output logic                      signal_state_o  // Signal state
    , output logic                      signal_valid_o  // Update is valid
    // Instruction load
    , output logic [INSTR_WIDTH-1:0] instr_data_o  // Instruction data
    , output logic                   instr_valid_o // Instruction valid
);

// Internal state
`DECLARE_DQ (1, fifo_pop,  clk_i, rst_i, 1'b0)

// Construct outputs
assign idle_o = fifo_empty && !msg_valid_i;

// Inbound FIFO - buffer incoming messages ready for digestion
logic                      fifo_empty, fifo_full;
logic [STREAM_WIDTH+2-1:0] fifo_data;

nx_fifo #(
      .DEPTH(           4)
    , .WIDTH(STREAM_WIDTH)
) msg_fifo (
      .clk_i    (clk_i)
    , .rst_i    (rst_i)
    // Write interface
    , .wr_data_i(msg_data_i                )
    , .wr_push_i(msg_valid_i && msg_ready_o)
    // Read interface
    , .rd_data_o(fifo_data )
    , .rd_pop_i (fifo_pop_q)
    // Status
    , .level_o(          )
    , .empty_o(fifo_empty)
    , .full_o (fifo_full )
);

assign msg_ready_o = ~fifo_full;

// Decode the next message
nx_message_t message;
assign message = fifo_data;

// - Extract output mapping from payload
`DECLARE_DQ($clog2(OUTPUTS), map_idx,     clk_i, rst_i, {$clog2(OUTPUTS){1'b0}})
`DECLARE_DQ( ADDR_ROW_WIDTH, map_tgt_row, clk_i, rst_i, { ADDR_ROW_WIDTH{1'b0}})
`DECLARE_DQ( ADDR_COL_WIDTH, map_tgt_col, clk_i, rst_i, { ADDR_COL_WIDTH{1'b0}})
`DECLARE_DQ( $clog2(INPUTS), map_tgt_idx, clk_i, rst_i, { $clog2(INPUTS){1'b0}})
`DECLARE_DQ(              1, map_tgt_seq, clk_i, rst_i,                    1'b0)
`DECLARE_DQ(              1, map_valid,   clk_i, rst_i,                    1'b0)

nx_msg_map_output_t msg_map_out;
assign msg_map_out = message;

assign map_idx     = msg_map_out.source_index;
assign map_tgt_row = msg_map_out.target_row;
assign map_tgt_col = msg_map_out.target_column;
assign map_tgt_idx = msg_map_out.target_index;
assign map_tgt_seq = msg_map_out.target_is_seq;

assign map_idx_o     = map_idx_q;
assign map_tgt_row_o = map_tgt_row_q;
assign map_tgt_col_o = map_tgt_col_q;
assign map_tgt_idx_o = map_tgt_idx_q;
assign map_tgt_seq_o = map_tgt_seq_q;
assign map_valid_o   = map_valid_q;

// - Extract signal state update from payload
`DECLARE_DQ($clog2(INPUTS), signal_index,  clk_i, rst_i, {$clog2(INPUTS){1'b0}})
`DECLARE_DQ(1,              signal_is_seq, clk_i, rst_i,                   1'b0)
`DECLARE_DQ(1,              signal_state,  clk_i, rst_i,                   1'b0)
`DECLARE_DQ(1,              signal_valid,  clk_i, rst_i,                   1'b0)

nx_msg_sig_state_t msg_sig_state;
assign msg_sig_state = message;

assign signal_index  = msg_sig_state.target_index;
assign signal_is_seq = msg_sig_state.target_is_seq;
assign signal_state  = msg_sig_state.state;

assign signal_index_o  = signal_index_q;
assign signal_is_seq_o = signal_is_seq_q;
assign signal_state_o  = signal_state_q;
assign signal_valid_o  = signal_valid_q;

// - Extract instruction load from payload
`DECLARE_DQ(INSTR_WIDTH, instr_data,  clk_i, rst_i, {INSTR_WIDTH{1'b0}})
`DECLARE_DQ(           , instr_valid, clk_i, rst_i,                1'b0)

nx_msg_load_instr_t msg_load_instr;
assign msg_load_instr = message;

assign instr_data = msg_load_instr.instruction;

assign instr_data_o  = instr_data_q;
assign instr_valid_o = instr_valid_q;

// Decode and routing
always_comb begin : p_decode
    // Working variables
    int idx;

    // Initialise state
    `INIT_D(fifo_pop);
    `INIT_D(map_valid);
    `INIT_D(signal_valid);
    `INIT_D(instr_valid);

    // Always clear interface valids (no backpressure on these interfaces)
    map_valid    = 1'b0;
    signal_valid = 1'b0;
    instr_valid  = 1'b0;

    // Decode the next entry in the FIFO
    if (!fifo_empty && !fifo_pop) begin
        // Pop the FIFO as the data has been picked up
        fifo_pop = 1'b1;

        instr_valid  = (message.header.command == NX_CMD_LOAD_INSTR);
        map_valid    = (message.header.command == NX_CMD_MAP_OUTPUT);
        signal_valid = (message.header.command == NX_CMD_SIG_STATE );

    // If not doing anything, clear the pop flag
    end else begin
        fifo_pop = 1'b0;

    end
end

endmodule : nx_msg_decoder
