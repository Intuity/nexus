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

// nx_stream_distributor
// Distributes to multiple outbound message streams
//
module nx_stream_distributor #(
      parameter STREAM_WIDTH = 32
    , parameter SKID_BUFFERS = "no"
) (
      input  logic                    clk_i
    , input  logic                    rst_i
    // Inbound message stream
    , input  logic [STREAM_WIDTH-1:0] dist_data_i
    , input  logic [             1:0] dist_dir_i
    , input  logic                    dist_valid_i
    , output logic                    dist_ready_o
    // Outbound distributed message streams
    // - North
    , output logic [STREAM_WIDTH-1:0] north_data_o
    , output logic                    north_valid_o
    , input  logic                    north_ready_i
    , input  logic                    north_present_i
    // - East
    , output logic [STREAM_WIDTH-1:0] east_data_o
    , output logic                    east_valid_o
    , input  logic                    east_ready_i
    , input  logic                    east_present_i
    // - South
    , output logic [STREAM_WIDTH-1:0] south_data_o
    , output logic                    south_valid_o
    , input  logic                    south_ready_i
    , input  logic                    south_present_i
    // - West
    , output logic [STREAM_WIDTH-1:0] west_data_o
    , output logic                    west_valid_o
    , input  logic                    west_ready_i
    , input  logic                    west_present_i
);

// Constants and enumerations
`include "nx_constants.svh"

// Pickup broadcast flags
logic broadcast;
assign broadcast = dist_data_i[STREAM_WIDTH-1];

// Skid buffer signals
logic [3:0][STREAM_WIDTH-1:0] skid_data;
logic [3:0]                   skid_valid, skid_ready;

// Construct outputs - if not broadcasting, then allow rerouting...
// - If NORTH absent route EAST
// - If EAST  absent route SOUTH
// - If SOUTH absent route WEST
// - If WEST  absent route NORTH

assign skid_data[0]  = dist_data_i;
assign skid_valid[0] = dist_valid_i && (
    (dist_dir_i == DIRX_NORTH &&  north_present_i              ) ||
    (dist_dir_i == DIRX_WEST  && !west_present_i  && !broadcast)
);

assign skid_data[1]   = dist_data_i;
assign skid_valid[1]  = dist_valid_i && (
    (dist_dir_i == DIRX_EAST  &&  east_present_i               ) ||
    (dist_dir_i == DIRX_NORTH && !north_present_i && !broadcast)
);

assign skid_data[2]  = dist_data_i;
assign skid_valid[2] = dist_valid_i && (
    (dist_dir_i == DIRX_SOUTH &&  south_present_i              ) ||
    (dist_dir_i == DIRX_EAST  && !east_present_i  && !broadcast)
);

assign skid_data[3]   = dist_data_i;
assign skid_valid[3]  = dist_valid_i && (
    (dist_dir_i == DIRX_WEST  &&  west_present_i               ) ||
    (dist_dir_i == DIRX_SOUTH && !south_present_i && !broadcast)
);

assign dist_ready_o = (
     (dist_dir_i == DIRX_NORTH) ? (skid_ready[0] && north_present_i || (skid_ready[1] || broadcast) && !north_present_i) :
    ((dist_dir_i == DIRX_EAST ) ? (skid_ready[1] && east_present_i  || (skid_ready[2] || broadcast) && !east_present_i ) :
    ((dist_dir_i == DIRX_SOUTH) ? (skid_ready[2] && south_present_i || (skid_ready[3] || broadcast) && !south_present_i) :
                                  (skid_ready[3] && west_present_i  || (skid_ready[0] || broadcast) && !west_present_i )))
);


// Skid buffers for each stream
generate
if (SKID_BUFFERS == "yes") begin
    nx_stream_skid #(
        .STREAM_WIDTH(STREAM_WIDTH)
    ) skid_north (
        .clk_i(clk_i)
        , .rst_i(rst_i)
        // Inbound stream
        , .inbound_data_i (skid_data[0] )
        , .inbound_valid_i(skid_valid[0])
        , .inbound_ready_o(skid_ready[0])
        // Outbound stream
        , .outbound_data_o (north_data_o )
        , .outbound_valid_o(north_valid_o)
        , .outbound_ready_i(north_ready_i)
    );

    nx_stream_skid #(
        .STREAM_WIDTH(STREAM_WIDTH)
    ) skid_east (
        .clk_i(clk_i)
        , .rst_i(rst_i)
        // Inbound stream
        , .inbound_data_i (skid_data[1] )
        , .inbound_valid_i(skid_valid[1])
        , .inbound_ready_o(skid_ready[1])
        // Outbound stream
        , .outbound_data_o (east_data_o )
        , .outbound_valid_o(east_valid_o)
        , .outbound_ready_i(east_ready_i)
    );

    nx_stream_skid #(
        .STREAM_WIDTH(STREAM_WIDTH)
    ) skid_south (
        .clk_i(clk_i)
        , .rst_i(rst_i)
        // Inbound stream
        , .inbound_data_i (skid_data[2] )
        , .inbound_valid_i(skid_valid[2])
        , .inbound_ready_o(skid_ready[2])
        // Outbound stream
        , .outbound_data_o (south_data_o )
        , .outbound_valid_o(south_valid_o)
        , .outbound_ready_i(south_ready_i)
    );

    nx_stream_skid #(
        .STREAM_WIDTH(STREAM_WIDTH)
    ) skid_west (
        .clk_i(clk_i)
        , .rst_i(rst_i)
        // Inbound stream
        , .inbound_data_i (skid_data[3] )
        , .inbound_valid_i(skid_valid[3])
        , .inbound_ready_o(skid_ready[3])
        // Outbound stream
        , .outbound_data_o (west_data_o )
        , .outbound_valid_o(west_valid_o)
        , .outbound_ready_i(west_ready_i)
    );
end else begin
    assign north_data_o  = skid_data[0];
    assign north_valid_o = skid_valid[0];
    assign skid_ready[0] = north_ready_i;

    assign east_data_o  = skid_data[1];
    assign east_valid_o = skid_valid[1];
    assign skid_ready[1] = east_ready_i;

    assign south_data_o  = skid_data[2];
    assign south_valid_o = skid_valid[2];
    assign skid_ready[2] = south_ready_i;

    assign west_data_o  = skid_data[3];
    assign west_valid_o = skid_valid[3];
    assign skid_ready[3] = west_ready_i;
end
endgenerate

endmodule : nx_stream_distributor
