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

// nx_stream_combiner
// Combines two directed streams, in different modes
//
module nx_stream_combiner #(
    parameter ARB_SCHEME = "round_robin" // round_robin, prefer_a, prefer_b
) (
      input  logic clk_i
    , input  logic rst_i
    // Inbound message streams
    // - A
    , input  nx_message_t stream_a_data_i
    , input  logic [1:0]  stream_a_dir_i
    , input  logic        stream_a_valid_i
    , output logic        stream_a_ready_o
    // - B
    , input  nx_message_t stream_b_data_i
    , input  logic [1:0]  stream_b_dir_i
    , input  logic        stream_b_valid_i
    , output logic        stream_b_ready_o
    // Outbound arbitrated message stream
    , output nx_message_t comb_data_o
    , output logic [1:0]  comb_dir_o
    , output logic        comb_valid_o
    , input  logic        comb_ready_i
);

// Arbitrated state
`DECLARE_DQT(nx_message_t, comb_data,  clk_i, rst_i, {$bits(nx_message_t){1'b0}})
`DECLARE_DQ (           2, comb_dir,   clk_i, rst_i, NX_DIRX_NORTH)
`DECLARE_DQ (           1, comb_valid, clk_i, rst_i, 1'b0)
`DECLARE_DQ (           1, comb_next,  clk_i, rst_i, 1'b0)
`DECLARE_DQ (           1, comb_curr,  clk_i, rst_i, 1'b0)

assign comb_data_o  = comb_data_q;
assign comb_dir_o   = comb_dir_q;
assign comb_valid_o = comb_valid_q;

// Connect inbound ready signals
assign stream_a_ready_o = (comb_curr == 1'b0) && (!comb_valid_q || comb_ready_i);
assign stream_b_ready_o = (comb_curr == 1'b1) && (!comb_valid_q || comb_ready_i);

// Arbitration
always_comb begin : p_arbitrate
    int   idx;
    logic search_start;
    logic found;

    `INIT_D(comb_data);
    `INIT_D(comb_dir);
    `INIT_D(comb_valid);
    `INIT_D(comb_next);
    `INIT_D(comb_curr);

    if (comb_ready_i) comb_valid = 1'b0;

    // Perform the arbitration
    if (!comb_valid) begin
        comb_curr = comb_next;
        if (comb_curr) begin
            comb_data  = stream_b_data_i;
            comb_dir   = stream_b_dir_i;
            comb_valid = stream_b_valid_i;
        end else begin
            comb_data  = stream_a_data_i;
            comb_dir   = stream_a_dir_i;
            comb_valid = stream_a_valid_i;
        end
    end

    // Set the search start point
    if      (ARB_SCHEME == "round_robin") search_start = comb_curr + 1'b1;
    else if (ARB_SCHEME == "prefer_a"   ) search_start = 1'b0;
    else if (ARB_SCHEME == "prefer_b"   ) search_start = 1'b1;

    // Search for the next direction
    found = 1'b0;
    for (idx = 0; idx < 2; idx = (idx + 1)) begin
        if (!found) begin
            case ({ search_start + idx[0], 1'b1 })
                { 1'b0, stream_a_valid_i }: begin
                    comb_next = 1'b0;
                    found     = 1'b1;
                end
                { 1'b1, stream_b_valid_i }: begin
                    comb_next = 1'b1;
                    found     = 1'b1;
                end
            endcase
        end
    end
end

endmodule : nx_stream_combiner
