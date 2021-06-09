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
// Arbitrates between different inbound message streams,
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

// Constants and enumerations
typedef enum logic [1:0] {
      NORTH
    , EAST
    , SOUTH
    , WEST
} arb_dir_t;

// Internal state
`DECLARE_DQ(2, choice, clk_i, rst_i, NORTH)
`DECLARE_DQ(1, locked, clk_i, rst_i, 1'b0)

// Construct outputs
// NOTE: This uses the combinatorial version of 'choice', not sequential!
assign arb_data_o = (
     (choice_q == NORTH) ? north_data_i :
    ((choice_q == EAST ) ? east_data_i  :
    ((choice_q == SOUTH) ? south_data_i :
                           west_data_i))
);
assign arb_valid_o = (
     (choice_q == NORTH) ? north_valid_i :
    ((choice_q == EAST ) ? east_valid_i  :
    ((choice_q == SOUTH) ? south_valid_i :
                           west_valid_i))
);
assign north_ready_o = arb_ready_i && (choice_q == NORTH);
assign east_ready_o  = arb_ready_i && (choice_q == EAST );
assign south_ready_o = arb_ready_i && (choice_q == SOUTH);
assign west_ready_o  = arb_ready_i && (choice_q == WEST );
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
                    NORTH: found = north_valid_i;
                    EAST : found = east_valid_i;
                    SOUTH: found = south_valid_i;
                    WEST : found = west_valid_i;
                endcase
                if (found) choice = (choice + idx[1:0] + 2'd1);
            end
        end
        locked = found;
    end
end

endmodule : nx_stream_arbiter
