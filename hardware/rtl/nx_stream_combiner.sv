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

// nx_stream_combiner
// Combines two directed streams
//
module nx_stream_combiner #(
    parameter STREAM_WIDTH = 32
) (
      input  logic                    clk_i
    , input  logic                    rst_i
    // Inbound message streams
    // - A
    , input  logic [STREAM_WIDTH-1:0] stream_a_data_i
    , input  logic [             1:0] stream_a_dir_i
    , input  logic                    stream_a_valid_i
    , output logic                    stream_a_ready_o
    // - B
    , input  logic [STREAM_WIDTH-1:0] stream_b_data_i
    , input  logic [             1:0] stream_b_dir_i
    , input  logic                    stream_b_valid_i
    , output logic                    stream_b_ready_o
    // Outbound arbitrated message stream
    , output logic [STREAM_WIDTH-1:0] comb_data_o
    , output logic [             1:0] comb_dir_o
    , output logic                    comb_valid_o
    , input  logic                    comb_ready_i
);

// Constants and enumerations
`include "nx_constants.svh"

// Internal state
`DECLARE_DQ(1, choice, clk_i, rst_i, 1'b0)
`DECLARE_DQ(1, locked, clk_i, rst_i, 1'b0)

// Construct outputs
assign comb_data_o  = choice_q ? stream_b_data_i  : stream_a_data_i;
assign comb_dir_o   = choice_q ? stream_b_dir_i   : stream_a_dir_i;
assign comb_valid_o = choice_q ? stream_b_valid_i : stream_a_valid_i;

assign stream_a_ready_o = comb_ready_i && (choice_q == 1'b0);
assign stream_b_ready_o = comb_ready_i && (choice_q == 1'b1);

// Arbitration
always_comb begin : p_arbitrate
    // Temporary variables
    int   idx;
    logic found;

    // Initialise
    `INIT_D(choice);
    `INIT_D(locked);

    // Clear lock if READY is high
    if (comb_ready_i) locked = 1'b0;

    // If not locked to a source, arbitrate using a round-robin
    if (!locked) begin
        found = 1'b0;
        for (idx = 0; idx < 2; idx = (idx + 1)) begin
            if (!found) begin
                case (choice + idx[0] + 1'b1)
                    1'b0: found = stream_a_valid_i;
                    1'b1: found = stream_b_valid_i;
                endcase
                if (found) choice = (choice + idx[0] + 1'b1);
            end
        end
        locked = found;
    end
end

endmodule : nx_stream_combiner
