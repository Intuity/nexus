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

// nx_stream_distributer
// Distributes to multiple outbound message streams
//
module nx_stream_distributer #(
    parameter STREAM_WIDTH = 32
) (
      input  logic                    clk_i
    , input  logic                    rst_i
    // Inbound message stream
    , output logic [STREAM_WIDTH-1:0] dist_data_i
    , output logic [             1:0] dist_dir_i
    , output logic                    dist_valid_i
    , input  logic                    dist_ready_o
    // Outbound distributed message streams
    // - North
    , input  logic [STREAM_WIDTH-1:0] north_data_o
    , input  logic                    north_valid_o
    , output logic                    north_ready_i
    // - East
    , input  logic [STREAM_WIDTH-1:0] east_data_o
    , input  logic                    east_valid_o
    , output logic                    east_ready_i
    // - South
    , input  logic [STREAM_WIDTH-1:0] south_data_o
    , input  logic                    south_valid_o
    , output logic                    south_ready_i
    // - West
    , input  logic [STREAM_WIDTH-1:0] west_data_o
    , input  logic                    west_valid_o
    , output logic                    west_ready_i
);

// Constants and enumerations
typedef enum logic [1:0] {
      NORTH
    , EAST
    , SOUTH
    , WEST
} dist_dir_t;

// Construct outputs
assign north_data_o  = dist_data_i;
assign north_valid_o = dist_valid_i && (dist_dir_i == NORTH);

assign east_data_o   = dist_data_i;
assign east_valid_o  = dist_valid_i && (dist_dir_i == EAST);

assign south_data_o  = dist_data_i;
assign south_valid_o = dist_valid_i && (dist_dir_i == SOUTH);

assign west_data_o   = dist_data_i;
assign west_valid_o  = dist_valid_i && (dist_dir_i == WEST);

assign dist_ready_o = (
     (dist_dir_i == NORTH) ? north_ready_i :
    ((dist_dir_i == EAST ) ? east_ready_i  :
    ((dist_dir_i == SOUTH) ? south_ready_i :
                             west_ready_i))
);

endmodule : nx_stream_distributer
