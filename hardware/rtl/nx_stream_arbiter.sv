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
    parameter STREAM_WIDTH = 32
) (
      input  logic                    clk_i
    , input  logic                    rst_i
    // Inbound message streams
    // - North
    , input  logic [STREAM_WIDTH-1:0] north_data_i
    , input  logic                    north_valid_i
    , output logic                    north_ready_o
    // - East
    , input  logic [STREAM_WIDTH-1:0] east_data_i
    , input  logic                    east_valid_i
    , output logic                    east_ready_o
    // - South
    , input  logic [STREAM_WIDTH-1:0] south_data_i
    , input  logic                    south_valid_i
    , output logic                    south_ready_o
    // - West
    , input  logic [STREAM_WIDTH-1:0] west_data_i
    , input  logic                    west_valid_i
    , output logic                    west_ready_o
    // Outbound arbitrated message stream
    , output logic [STREAM_WIDTH-1:0] arb_data_o
    , output logic [             1:0] arb_dir_o
    , output logic                    arb_valid_o
    , input  logic                    arb_ready_i
);

// Arbitrated state
`DECLARE_DQ(STREAM_WIDTH, arb_data,  clk_i, rst_i, {STREAM_WIDTH{1'b0}})
`DECLARE_DQ(           1, arb_valid, clk_i, rst_i, 1'b0)
`DECLARE_DQ(           2, arb_next,  clk_i, rst_i, NX_DIRX_NORTH)
`DECLARE_DQ(           2, arb_curr,  clk_i, rst_i, NX_DIRX_NORTH)

// Connect outputs
assign arb_data_o  = arb_data_q;
assign arb_dir_o   = arb_curr_q;
assign arb_valid_o = arb_valid_q;

assign north_ready_o = (arb_curr == NX_DIRX_NORTH) && (!arb_valid_q || arb_ready_i);
assign east_ready_o  = (arb_curr == NX_DIRX_EAST ) && (!arb_valid_q || arb_ready_i);
assign south_ready_o = (arb_curr == NX_DIRX_SOUTH) && (!arb_valid_q || arb_ready_i);
assign west_ready_o  = (arb_curr == NX_DIRX_WEST ) && (!arb_valid_q || arb_ready_i);

// Arbitration
always_comb begin : p_arbitrate
    int   idx;
    logic found;

    `INIT_D(arb_data);
    `INIT_D(arb_valid);
    `INIT_D(arb_next);
    `INIT_D(arb_curr);

    if (arb_ready_i) arb_valid = 1'b0;

    // Perform the arbitration
    if (!arb_valid) begin
        arb_curr = arb_next;
        case (arb_curr)
            NX_DIRX_NORTH: begin
                arb_data  = north_data_i;
                arb_valid = north_valid_i;
            end
            NX_DIRX_EAST: begin
                arb_data  = east_data_i;
                arb_valid = east_valid_i;
            end
            NX_DIRX_SOUTH: begin
                arb_data  = south_data_i;
                arb_valid = south_valid_i;
            end
            NX_DIRX_WEST: begin
                arb_data  = west_data_i;
                arb_valid = west_valid_i;
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
