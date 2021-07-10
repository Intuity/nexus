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

// nx_stream_arbiter
// Arbitrates between multiple inbound message streams
//
module nx_stream_arbiter #(
      parameter STREAM_WIDTH = 32
    , parameter SKID_BUFFERS = "no"
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

// Constants and enumerations
`include "nx_constants.svh"

// Internal state
`DECLARE_DQ(2, choice, clk_i, rst_i, DIRX_NORTH)
`DECLARE_DQ(1, locked, clk_i, rst_i, 1'b0)

// Skid buffers for each stream
logic [3:0][STREAM_WIDTH-1:0] skid_data;
logic [3:0]                   skid_valid, skid_ready;

generate
if (SKID_BUFFERS == "yes") begin
nx_stream_skid #(
    .STREAM_WIDTH(STREAM_WIDTH)
) skid_north (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Inbound stream
    , .inbound_data_i (north_data_i )
    , .inbound_valid_i(north_valid_i)
    , .inbound_ready_o(north_ready_o)
    // Outbound stream
    , .outbound_data_o (skid_data[0] )
    , .outbound_valid_o(skid_valid[0])
    , .outbound_ready_i(skid_ready[0])
);

nx_stream_skid #(
    .STREAM_WIDTH(STREAM_WIDTH)
) skid_east (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Inbound stream
    , .inbound_data_i (east_data_i )
    , .inbound_valid_i(east_valid_i)
    , .inbound_ready_o(east_ready_o)
    // Outbound stream
    , .outbound_data_o (skid_data[1] )
    , .outbound_valid_o(skid_valid[1])
    , .outbound_ready_i(skid_ready[1])
);

nx_stream_skid #(
    .STREAM_WIDTH(STREAM_WIDTH)
) skid_south (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Inbound stream
    , .inbound_data_i (south_data_i )
    , .inbound_valid_i(south_valid_i)
    , .inbound_ready_o(south_ready_o)
    // Outbound stream
    , .outbound_data_o (skid_data[2] )
    , .outbound_valid_o(skid_valid[2])
    , .outbound_ready_i(skid_ready[2])
);

nx_stream_skid #(
    .STREAM_WIDTH(STREAM_WIDTH)
) skid_west (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Inbound stream
    , .inbound_data_i (west_data_i )
    , .inbound_valid_i(west_valid_i)
    , .inbound_ready_o(west_ready_o)
    // Outbound stream
    , .outbound_data_o (skid_data[3] )
    , .outbound_valid_o(skid_valid[3])
    , .outbound_ready_i(skid_ready[3])
);
end else begin
    assign skid_data[0]  = north_data_i;
    assign skid_valid[0] = north_valid_i;
    assign north_ready_o = skid_ready[0];

    assign skid_data[1]  = east_data_i;
    assign skid_valid[1] = east_valid_i;
    assign east_ready_o  = skid_ready[1];

    assign skid_data[2]  = south_data_i;
    assign skid_valid[2] = south_valid_i;
    assign south_ready_o = skid_ready[2];

    assign skid_data[3]  = west_data_i;
    assign skid_valid[3] = west_valid_i;
    assign west_ready_o  = skid_ready[3];
end
endgenerate

// Construct outputs
assign arb_data_o = (
     (choice_q == DIRX_NORTH) ? skid_data[0] :
    ((choice_q == DIRX_EAST ) ? skid_data[1] :
    ((choice_q == DIRX_SOUTH) ? skid_data[2] :
                                skid_data[3]))
);
assign arb_valid_o = (
     (choice_q == DIRX_NORTH) ? skid_valid[0] :
    ((choice_q == DIRX_EAST ) ? skid_valid[1] :
    ((choice_q == DIRX_SOUTH) ? skid_valid[2] :
                                skid_valid[3]))
);
assign skid_ready[0] = arb_ready_i && (!locked || choice_q == DIRX_NORTH);
assign skid_ready[1] = arb_ready_i && (!locked || choice_q == DIRX_EAST );
assign skid_ready[2] = arb_ready_i && (!locked || choice_q == DIRX_SOUTH);
assign skid_ready[3] = arb_ready_i && (!locked || choice_q == DIRX_WEST );
assign arb_dir_o     = choice_q;

// Arbitration
always_comb begin : p_arbitrate
    // Temporary variables
    int   idx;
    logic found;

    // Initialise
    `INIT_D(choice);
    `INIT_D(locked);

    // Clear lock if READY is high
    if (arb_ready_i) locked = 1'b0;

    // If not locked to a source, arbitrate using a round-robin
    if (!locked) begin
        found = 1'b0;
        for (idx = 0; idx < 4; idx = (idx + 1)) begin
            if (!found) begin
                case (choice + idx[1:0] + 2'd1)
                    DIRX_NORTH: found = skid_valid[0];
                    DIRX_EAST : found = skid_valid[1];
                    DIRX_SOUTH: found = skid_valid[2];
                    DIRX_WEST : found = skid_valid[3];
                endcase
                if (found) choice = (choice + idx[1:0] + 2'd1);
            end
        end
        locked = found;
    end
end

endmodule : nx_stream_arbiter
