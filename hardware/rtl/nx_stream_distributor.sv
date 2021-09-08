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
module nx_stream_distributor
import NXConstants::*;
(
      input  logic clk_i
    , input  logic rst_i
    // Idle flag
    , output logic idle_o
    // Inbound message stream
    , input  node_message_t dist_data_i
    , input  direction_t    dist_dir_i
    , input  logic          dist_valid_i
    , output logic          dist_ready_o
    // Outbound distributed message streams
    // - North
    , output node_message_t north_data_o
    , output logic          north_valid_o
    , input  logic          north_ready_i
    , input  logic          north_present_i
    // - East
    , output node_message_t east_data_o
    , output logic          east_valid_o
    , input  logic          east_ready_i
    , input  logic          east_present_i
    // - South
    , output node_message_t south_data_o
    , output logic          south_valid_o
    , input  logic          south_ready_i
    , input  logic          south_present_i
    // - West
    , output node_message_t west_data_o
    , output logic          west_valid_o
    , input  logic          west_ready_i
    , input  logic          west_present_i
);

// Bind outbound ports into arrays
node_message_t egress_data [3:0];
logic [3:0] egress_ready, egress_present, egress_full, egress_empty;

assign { north_data_o, north_valid_o } = { egress_data[DIRECTION_NORTH], !egress_empty[DIRECTION_NORTH] };
assign { east_data_o,  east_valid_o  } = { egress_data[DIRECTION_EAST ], !egress_empty[DIRECTION_EAST ] };
assign { south_data_o, south_valid_o } = { egress_data[DIRECTION_SOUTH], !egress_empty[DIRECTION_SOUTH] };
assign { west_data_o,  west_valid_o  } = { egress_data[DIRECTION_WEST ], !egress_empty[DIRECTION_WEST ] };

assign egress_ready[DIRECTION_NORTH] = north_ready_i;
assign egress_ready[DIRECTION_EAST ] = east_ready_i;
assign egress_ready[DIRECTION_SOUTH] = south_ready_i;
assign egress_ready[DIRECTION_WEST ] = west_ready_i;

assign egress_present[DIRECTION_NORTH] = north_present_i;
assign egress_present[DIRECTION_EAST ] = east_present_i;
assign egress_present[DIRECTION_SOUTH] = south_present_i;
assign egress_present[DIRECTION_WEST ] = west_present_i;

generate
for (genvar i = 0; i < 4; i = (i + 1)) begin
    logic primary_active;
    logic aliased_active;

    assign primary_active = (dist_dir_i == i) && egress_present[i];

    if (i == DIRECTION_NORTH) begin
        assign aliased_active = (dist_dir_i == DIRECTION_WEST) && !egress_present[DIRECTION_WEST];
    end else if (i == DIRECTION_EAST ) begin
        assign aliased_active = (dist_dir_i == DIRECTION_NORTH) && !egress_present[DIRECTION_NORTH];
    end else if (i == DIRECTION_SOUTH) begin
        assign aliased_active = (dist_dir_i == DIRECTION_EAST) && !egress_present[DIRECTION_EAST];
    end else if (i == DIRECTION_WEST ) begin
        assign aliased_active = (dist_dir_i == DIRECTION_SOUTH) && !egress_present[DIRECTION_SOUTH];
    end

    nx_fifo #(
          .DEPTH(2)
        , .WIDTH($bits(node_message_t))
    ) egress_fifo (
          .clk_i(clk_i)
        , .rst_i(rst_i)
        // Write interface
        , .wr_data_i(dist_data_i)
        , .wr_push_i(
            dist_valid_i && !egress_full[i] && (primary_active || aliased_active)
        )
        // Read interface
        , .rd_data_o(egress_data[i])
        , .rd_pop_i (!egress_empty[i] && egress_ready[i])
        // Status
        , .level_o(               )
        , .empty_o(egress_empty[i])
        , .full_o (egress_full[i] )
    );
end
endgenerate

// Drive inbound stream ready
assign dist_ready_o = (
    (dist_dir_i == DIRECTION_NORTH && (
        (!egress_full[DIRECTION_NORTH] &&  egress_present[DIRECTION_NORTH]) ||
        (!egress_full[DIRECTION_EAST ] && !egress_present[DIRECTION_NORTH])
    )) ||
    (dist_dir_i == DIRECTION_EAST && (
        (!egress_full[DIRECTION_EAST ] &&  egress_present[DIRECTION_EAST ]) ||
        (!egress_full[DIRECTION_SOUTH] && !egress_present[DIRECTION_EAST ])
    )) ||
    (dist_dir_i == DIRECTION_SOUTH && (
        (!egress_full[DIRECTION_SOUTH] &&  egress_present[DIRECTION_SOUTH]) ||
        (!egress_full[DIRECTION_WEST ] && !egress_present[DIRECTION_SOUTH])
    )) ||
    (dist_dir_i == DIRECTION_WEST && (
        (!egress_full[DIRECTION_WEST ] &&  egress_present[DIRECTION_WEST ]) ||
        (!egress_full[DIRECTION_NORTH] && !egress_present[DIRECTION_WEST ])
    ))
);

// Detect idleness
assign idle_o = (&egress_empty) && !dist_valid_i;

endmodule : nx_stream_distributor
