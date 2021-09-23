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

localparam SECT_SIZE  = 8;
localparam NUM_SECTS  = (WIDTH + SECT_SIZE - 1) / SECT_SIZE;
localparam SECT_WIDTH = $clog2(SECT_SIZE) + 1;

// Reverse the scalar to count from the LSB upwards
logic [WIDTH-1:0] reversed;

generate
for (genvar idx = 0; idx < WIDTH; idx++) begin : gen_reverse
    assign reversed[idx] = REVERSE_INPUT ? scalar_i[idx] : scalar_i[WIDTH-idx-1];
end
endgenerate

// Pad out to a full number of sections
logic [(NUM_SECTS*SECT_SIZE)-1:0] padded;
assign padded = { {((NUM_SECTS*SECT_SIZE)-WIDTH){1'b0}}, reversed };

// Count each section
logic [NUM_SECTS-1:0]                 active;
logic [NUM_SECTS-1:0][SECT_WIDTH-1:0] sections;

generate
for (genvar idx = 0; idx < NUM_SECTS; idx++) begin
    always_comb begin : comb_set_count
        active[idx] = |(padded[((idx+1)*SECT_SIZE)-1:idx*SECT_SIZE]);
        casex (padded[((idx+1)*SECT_SIZE)-1:idx*SECT_SIZE])
            'b????_???1: sections[idx] = 'd0;
            'b????_??10: sections[idx] = 'd1;
            'b????_?100: sections[idx] = 'd2;
            'b????_1000: sections[idx] = 'd3;
            'b???1_0000: sections[idx] = 'd4;
            'b??10_0000: sections[idx] = 'd5;
            'b?100_0000: sections[idx] = 'd6;
            'b1000_0000: sections[idx] = 'd7;
            'b0000_0000: sections[idx] = 'd8;
        endcase
    end
end
endgenerate

// Add up the full amount
logic [NUM_SECTS-1:0]                  stop_sum;
logic [NUM_SECTS-1:0][COUNT_WIDTH-1:0] summations;

generate
for (genvar idx = 0; idx < NUM_SECTS; idx++) begin : gen_summation
    if (idx > 0) begin
        assign stop_sum[idx]   = stop_sum[idx-1] || active[idx];
        assign summations[idx] = (
            summations[idx-1] + (stop_sum[idx-1] ? 'd0 : COUNT_WIDTH'(sections[idx]))
        );
    end else begin
        assign stop_sum[idx]   = active[idx];
        assign summations[idx] = COUNT_WIDTH'(sections[idx]);
    end
end
endgenerate

// Drive output from final sum
assign leading_o = summations[NUM_SECTS-1];

endmodule : nx_clz
