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

// Use an ingress FIFO to ease timing
logic [STREAM_WIDTH-1:0] ingress_data;
logic [             1:0] ingress_dir;
logic                    ingress_pop, ingress_empty, ingress_full;

assign dist_ready_o = !ingress_full;

nx_fifo #(
      .DEPTH(2)
    , .WIDTH(STREAM_WIDTH + 2)
) ingress_fifo (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Write interface
    , .wr_data_i({ dist_data_i, dist_dir_i })
    , .wr_push_i(dist_valid_i && !ingress_full)
    // Read interface
    , .rd_data_o({ ingress_data, ingress_dir })
    , .rd_pop_i (ingress_pop)
    // Status
    , .level_o(             )
    , .empty_o(ingress_empty)
    , .full_o (ingress_full )
);

// Outbound stream interfaces
`DECLARE_DQ_ARRAY(STREAM_WIDTH, 4, ob_data,  clk_i, rst_i, {STREAM_WIDTH{1'b0}})
`DECLARE_DQ_ARRAY(           1, 4, ob_valid, clk_i, rst_i, 1'b0)

assign {
    north_data_o, east_data_o, south_data_o, west_data_o
} = { ob_data_q[0], ob_data_q[1], ob_data_q[2], ob_data_q[3] };

assign {
    north_valid_o, east_valid_o, south_valid_o, west_valid_o
} = { ob_valid_q[0], ob_valid_q[1], ob_valid_q[2], ob_valid_q[3] };

logic [3:0] ob_ready;
assign ob_ready = { west_ready_i, south_ready_i, east_ready_i, north_ready_i };

always_comb begin : p_distribute
    int         i;
    logic [1:0] remap_dir;

    `INIT_D_ARRAY(ob_data);
    `INIT_D_ARRAY(ob_valid);

    // Always clear pop
    ingress_pop = 1'b0;

    // Clear any valids where the ready is high
    for (i = 0; i < 4; i = (i + 1)) begin
        if (ob_ready[i]) ob_valid[i] = 1'b0;
    end

    // Remap the direction based on output presence
    case ({ ingress_dir, 1'b0 })
        { NX_DIRX_NORTH, north_present_i }: remap_dir = NX_DIRX_EAST;
        { NX_DIRX_EAST,  east_present_i  }: remap_dir = NX_DIRX_SOUTH;
        { NX_DIRX_SOUTH, south_present_i }: remap_dir = NX_DIRX_WEST;
        { NX_DIRX_WEST,  west_present_i  }: remap_dir = NX_DIRX_NORTH;
        default                           : remap_dir = ingress_dir;
    endcase

    // Arbitrate the next output
    if (!ingress_empty && !ob_valid[remap_dir]) begin
        ob_data[remap_dir]  = ingress_data;
        ob_valid[remap_dir] = 1'b1;
        ingress_pop         = 1'b1;
    end
end

endmodule : nx_stream_distributor
