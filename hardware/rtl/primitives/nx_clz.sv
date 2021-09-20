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

// nx_clz
// Leading-zero counter
//
module nx_clz #(
      parameter WIDTH         = 8                 // How many bits in the input
    , parameter REVERSE_INPUT = 1'b0              // Whether to reverse input bits
    , parameter COUNT_WIDTH   = $clog2(WIDTH) + 1 // Required counter width
) (
      input  logic [WIDTH-1:0]       scalar_i
    , output logic [COUNT_WIDTH-1:0] leading_o
);

localparam PAIRS = (WIDTH + 1) / 2;

// Reverse input if required
logic [WIDTH-1:0] normalised;

generate
if (REVERSE_INPUT) begin
    for (genvar idx = 0; idx < WIDTH; idx++) begin : gen_reverse
        assign normalised[WIDTH-idx-1] = scalar_i[idx];
    end
end else begin
    assign normalised = scalar_i;
end
endgenerate

// Encode each pairing of bits
logic [PAIRS-1:0][1:0] encoded;

generate
for (genvar idx = 0; idx < PAIRS; idx++) begin : gen_encode
    assign encoded[idx] = (
        (normalised[(idx*2)+:2] == 2'b00) ? 2'd2 : ( // Two leading zeroes
        (normalised[(idx*2)+:2] == 2'b01) ? 2'd1 : ( // One leading zero
                                            2'd0     // No leading zeroes
    )));
end
endgenerate

// Sum up the encodings
logic [PAIRS-1:0][COUNT_WIDTH-1:0] summations;

generate
for (genvar idx = 0; idx < PAIRS; idx++) begin : gen_summation
    if (idx > 0) begin
        assign summations[idx] = encoded[idx] + (encoded[idx][1] ? summations[idx-1] : 'd0);
    end else begin
        assign summations[idx] = encoded[idx];
    end
end
endgenerate

// Drive output from final sum
assign leading_o = summations[PAIRS-1];

endmodule : nx_clz
