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

// nx_stream_arbiter
// Arbitrates between multiple inbound message streams
//
module nx_stream_arbiter #(
      parameter ADDR_ROW_WIDTH = 4
    , parameter ADDR_COL_WIDTH = 4
) (
      input  logic clk_i
    , input  logic rst_i
    // Control signals
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
    // Inbound message streams
    // - North
    , input  nx_message_t north_data_i
    , input  logic        north_valid_i
    , output logic        north_ready_o
    // - East
    , input  nx_message_t east_data_i
    , input  logic        east_valid_i
    , output logic        east_ready_o
    // - South
    , input  nx_message_t south_data_i
    , input  logic        south_valid_i
    , output logic        south_ready_o
    // - West
    , input  nx_message_t west_data_i
    , input  logic        west_valid_i
    , output logic        west_ready_o
    // Outbound stream for this node
    , output nx_message_t internal_data_o
    , output logic        internal_valid_o
    , input  logic        internal_ready_i
    // Outbound stream for bypass
    , output nx_message_t   bypass_data_o
    , output nx_direction_t bypass_dir_o
    , output logic          bypass_valid_o
    , input  logic          bypass_ready_i
);

// Arbitrated state
`DECLARE_DQT(  nx_message_t, arb_data,           clk_i, rst_i, {$bits(nx_message_t){1'b0}})
`DECLARE_DQ (             1, arb_internal_valid, clk_i, rst_i, 1'b0)
`DECLARE_DQ (             1, arb_bypass_valid,   clk_i, rst_i, 1'b0)
`DECLARE_DQT(nx_direction_t, arb_next,           clk_i, rst_i, NX_DIRX_NORTH)
`DECLARE_DQT(nx_direction_t, arb_curr,           clk_i, rst_i, NX_DIRX_NORTH)

// Detect matches from each data stream
logic north_match, east_match, south_match, west_match;

assign north_match = (north_data_i.header.row == node_row_i && north_data_i.header.column == node_col_i);
assign east_match  = (east_data_i.header.row  == node_row_i && east_data_i.header.column  == node_col_i);
assign south_match = (south_data_i.header.row == node_row_i && south_data_i.header.column == node_col_i);
assign west_match  = (west_data_i.header.row  == node_row_i && west_data_i.header.column  == node_col_i);

// Connect internal output
assign internal_data_o  = arb_data_q;
assign internal_valid_o = arb_internal_valid_q;

// Connect bypass output
assign bypass_data_o  = arb_data_q;
assign bypass_valid_o = arb_bypass_valid_q;
assign bypass_dir_o   = (
    (arb_data_q.header.row    > node_row_i) ? NX_DIRX_SOUTH : (
    (arb_data_q.header.row    < node_row_i) ? NX_DIRX_NORTH : (
    (arb_data_q.header.column > node_col_i) ? NX_DIRX_EAST  : (
                                              NX_DIRX_WEST    )))
);

// Connect inbound ready signals
logic both_ready;
assign both_ready = (
    (!arb_internal_valid_q || internal_ready_i) &&
    (!arb_bypass_valid_q   || bypass_ready_i  )
);
assign north_ready_o = (arb_curr == NX_DIRX_NORTH) && both_ready;
assign east_ready_o  = (arb_curr == NX_DIRX_EAST ) && both_ready;
assign south_ready_o = (arb_curr == NX_DIRX_SOUTH) && both_ready;
assign west_ready_o  = (arb_curr == NX_DIRX_WEST ) && both_ready;

// Arbitration
always_comb begin : p_arbitrate
    int   idx;
    logic found;

    `INIT_D(arb_data);
    `INIT_D(arb_internal_valid);
    `INIT_D(arb_bypass_valid);
    `INIT_D(arb_next);
    `INIT_D(arb_curr);

    if (internal_ready_i) arb_internal_valid = 1'b0;
    if (bypass_ready_i  ) arb_bypass_valid   = 1'b0;

    // Perform the arbitration
    if (!arb_internal_valid && !arb_bypass_valid) begin
        arb_curr = arb_next;
        case (arb_curr)
            NX_DIRX_NORTH: begin
                arb_data           = north_data_i;
                arb_internal_valid = north_valid_i &&  north_match;
                arb_bypass_valid   = north_valid_i && !north_match;
            end
            NX_DIRX_EAST: begin
                arb_data           = east_data_i;
                arb_internal_valid = east_valid_i &&  east_match;
                arb_bypass_valid   = east_valid_i && !east_match;
            end
            NX_DIRX_SOUTH: begin
                arb_data           = south_data_i;
                arb_internal_valid = south_valid_i &&  south_match;
                arb_bypass_valid   = south_valid_i && !south_match;
            end
            NX_DIRX_WEST: begin
                arb_data           = west_data_i;
                arb_internal_valid = west_valid_i &&  west_match;
                arb_bypass_valid   = west_valid_i && !west_match;
            end
        endcase
    end

    // Search for the next direction
    found = 1'b0;
    for (idx = 0; idx < 4; idx = (idx + 1)) begin
        if (!found) begin
            case ({ arb_curr + idx[1:0] + 2'd1, 1'b1 })
                { NX_DIRX_NORTH, north_valid_i }: begin
                    arb_next = NX_DIRX_NORTH;
                    found    = 1'b1;
                end
                { NX_DIRX_EAST, east_valid_i }: begin
                    arb_next = NX_DIRX_EAST;
                    found    = 1'b1;
                end
                { NX_DIRX_SOUTH, south_valid_i }: begin
                    arb_next = NX_DIRX_SOUTH;
                    found    = 1'b1;
                end
                { NX_DIRX_WEST, west_valid_i }: begin
                    arb_next = NX_DIRX_WEST;
                    found    = 1'b1;
                end
            endcase
        end
    end
end

endmodule : nx_stream_arbiter
