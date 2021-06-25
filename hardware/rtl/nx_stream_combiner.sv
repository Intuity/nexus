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

// nx_stream_combiner
// Combines two directed streams, in different modes
//
module nx_stream_combiner #(
      parameter STREAM_WIDTH = 32
    , parameter ARB_SCHEME   = "round_robin" // round_robin, prefer_a, prefer_b
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

// State
logic active, next, last, lock;

// Output wiring
assign comb_data_o  = active ? stream_b_data_i  : stream_a_data_i;
assign comb_dir_o   = active ? stream_b_dir_i   : stream_a_dir_i;
assign comb_valid_o = active ? stream_b_valid_i : stream_a_valid_i;

assign stream_a_ready_o = comb_ready_i && (active == 1'b0);
assign stream_b_ready_o = comb_ready_i && (active == 1'b1);

// Arbitration
generate
if (ARB_SCHEME == "round_robin") begin
    assign next = !last || !stream_a_valid_i;
end else if (ARB_SCHEME == "prefer_a") begin
    assign next = !stream_a_valid_i;
end else if (ARB_SCHEME == "prefer_b") begin
    assign next = stream_b_valid_i;
end
endgenerate

// Sequential logic
always_ff @(posedge clk_i, posedge rst_i) begin : p_arb
    if (rst_i) begin
        active <= 1'b0;
        last   <= 1'b0;
        lock   <= 1'b0;
    end else begin
        if (!lock || comb_ready_i) begin
            last   <= active;
            active <= next;
            lock   <= next ? stream_b_valid_i : stream_a_valid_i;
        end
    end
end

endmodule : nx_stream_combiner
