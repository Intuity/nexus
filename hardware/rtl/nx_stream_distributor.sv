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
    // - East
    , output logic [STREAM_WIDTH-1:0] east_data_o
    , output logic                    east_valid_o
    , input  logic                    east_ready_i
    // - South
    , output logic [STREAM_WIDTH-1:0] south_data_o
    , output logic                    south_valid_o
    , input  logic                    south_ready_i
    // - West
    , output logic [STREAM_WIDTH-1:0] west_data_o
    , output logic                    west_valid_o
    , input  logic                    west_ready_i
);

// Constants and enumerations
`include "nx_constants.svh"

// Construct outputs
assign north_data_o  = dist_data_i;
assign north_valid_o = dist_valid_i && (dist_dir_i == DIRX_NORTH);

assign east_data_o   = dist_data_i;
assign east_valid_o  = dist_valid_i && (dist_dir_i == DIRX_EAST);

assign south_data_o  = dist_data_i;
assign south_valid_o = dist_valid_i && (dist_dir_i == DIRX_SOUTH);

assign west_data_o   = dist_data_i;
assign west_valid_o  = dist_valid_i && (dist_dir_i == DIRX_WEST);

assign dist_ready_o = (
     (dist_dir_i == DIRX_NORTH) ? north_ready_i :
    ((dist_dir_i == DIRX_EAST ) ? east_ready_i  :
    ((dist_dir_i == DIRX_SOUTH) ? south_ready_i :
                                  west_ready_i))
);

endmodule : nx_stream_distributor
