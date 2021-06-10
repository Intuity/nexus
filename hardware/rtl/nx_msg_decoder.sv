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
module nx_msg_decoder #(
      parameter STREAM_WIDTH   = 32
    , parameter ADDR_ROW_WIDTH =  4
    , parameter ADDR_COL_WIDTH =  4
    , parameter COMMAND_WIDTH  =  2
) (
      input  logic clk_i
    , input  logic rst_i
    // Node identity
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
    // Inbound message stream
    , input  logic [STREAM_WIDTH-1:0] msg_data_i
    , input  logic [             1:0] msg_dir_i
    , input  logic                    msg_valid_i
    , output logic                    msg_ready_o
    // Outbound bypass message stream
    , output logic [STREAM_WIDTH-1:0] bypass_data_o
    , output logic [             1:0] bypass_dir_o
    , output logic                    bypass_valid_o
    , input  logic                    bypass_ready_i
);

// Parameters and constants
localparam BC_DECAY_WIDTH = ADDR_ROW_WIDTH + ADDR_COL_WIDTH;
localparam PAYLOAD_WIDTH  = (
    STREAM_WIDTH - 1 - ADDR_ROW_WIDTH - ADDR_COL_WIDTH - COMMAND_WIDTH
);

`include "nx_constants.svh"

// Internal state
`DECLARE_DQ(4,            send_dir,  clk_i, rst_i, 4'd0)
`DECLARE_DQ(1,            fifo_pop,  clk_i, rst_i, 1'b0)
`DECLARE_DQ(STREAM_WIDTH, byp_data,  clk_i, rst_i, {STREAM_WIDTH{1'b0}})
`DECLARE_DQ(2,            byp_dir,   clk_i, rst_i, 2'b0)
`DECLARE_DQ(1,            byp_valid, clk_i, rst_i, 1'b0)

// Construct outputs
assign bypass_data_o  = byp_data_q;
assign bypass_dir_o   = byp_dir_q;
assign bypass_valid_o = byp_valid_q;

// Inbound FIFO - buffer incoming messages ready for digestion
logic                      fifo_empty, fifo_full;
logic [STREAM_WIDTH+2-1:0] fifo_data;

nx_fifo #(
      .DEPTH(             2)
    , .WIDTH(STREAM_WIDTH+2)
) msg_fifo (
      .clk_i    (clk_i)
    , .rst_i    (rst_i)
    // Write interface
    , .wr_data_i({msg_dir_i, msg_data_i}   )
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
nx_direction_t             arrival_dir;
logic                      broadcast;
logic [ADDR_ROW_WIDTH-1:0] addr_row;
logic [ADDR_COL_WIDTH-1:0] addr_col;
logic [BC_DECAY_WIDTH-1:0] bc_decay;
logic [ COMMAND_WIDTH-1:0] command;
logic [ PAYLOAD_WIDTH-1:0] payload;

assign { arrival_dir, broadcast, addr_row, addr_col, command, payload } = fifo_data;
assign bc_decay = { addr_row, addr_col };

always_comb begin : p_decode
    // Working variables
    int idx;

    // Initialise state
    `INIT_D(send_dir);
    `INIT_D(fifo_pop);
    `INIT_D(byp_data);
    `INIT_D(byp_dir);
    `INIT_D(byp_valid);

    // If bypass data accepted, clear the valid and direction flag
    if (byp_valid && bypass_ready_i) begin
        byp_valid         = 1'b0;
        send_dir[byp_dir] = 1'b0;
    end

    // Decode the next entry in the FIFO
    if (!send_dir && !fifo_empty && !fifo_pop) begin
        // Pop the FIFO as the data has been picked up
        fifo_pop = 1'b1;

        // This node needs to handle the message
        if (broadcast || (addr_row == node_row_i && addr_col == node_col_i)) begin
            case (command)
                CMD_LOAD_INSTR: begin

                end
                CMD_CFG_INPUT: begin

                end
                CMD_CFG_OUTPUT: begin

                end
                CMD_SIG_STATE: begin

                end
            endcase
        end

        // Does this message need to be sent on to anyone else?
        if (
            ( broadcast && bc_decay > {BC_DECAY_WIDTH{1'b0}}) ||
            (!broadcast && (addr_row != node_row_i || addr_col != node_col_i))
        ) begin
            // Mark the directions to send in
            if (broadcast) begin
                case (arrival_dir)                  // W  S  E  N
                    DIRX_NORTH: send_dir = 4'b1110; // X  X  X
                    DIRX_EAST : send_dir = 4'b1000; // X
                    DIRX_SOUTH: send_dir = 4'b1011; // X     X  X
                    DIRX_WEST : send_dir = 4'b0010; //       X
                endcase
            end else if (addr_row < node_row_i) begin
                send_dir = 4'b0001; // Send north
            end else if (addr_row > node_row_i) begin
                send_dir = 4'b0100; // Send south
            end else if (addr_col < node_col_i) begin
                send_dir = 4'b1000; // Send west
            end else if (addr_col > node_col_i) begin
                send_dir = 4'b0010; // Send east
            end
            // Setup the data to send
            byp_data = (
                broadcast ? {
                    broadcast,
                    bc_decay - { {(BC_DECAY_WIDTH-1){1'b0}}, 1'b1 },
                    command,
                    payload
                }
                : fifo_data
            );
        end

    // If not doing anything, clear the pop flag
    end else begin
        fifo_pop = 1'b0;

    end

    // Are there any outstanding messages to be sent?
    for (idx = 0; idx < 4; idx = (idx + 1)) begin
        if (!byp_valid && send_dir[idx]) begin
            byp_dir   = idx;
            byp_valid = 1'b1;
        end
    end
end

endmodule : nx_msg_decoder
