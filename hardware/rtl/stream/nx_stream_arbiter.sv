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
// Arbitrates between multiple inbound message streams
//
module nx_stream_arbiter
import NXConstants::*;
#(
      parameter STREAMS = 4
    , parameter SCHEME  = nx_primitives::ROUND_ROBIN
) (
      input  logic                                  i_clk
    , input  logic                                  i_rst
    // Inbound message streams
    // NOTE: Icarus Verilog only works with explicit multi-dimensional array
    , input  logic [STREAMS-1:0][MESSAGE_WIDTH-1:0] i_inbound_data
    , input  logic [STREAMS-1:0]                    i_inbound_valid
    , output logic [STREAMS-1:0]                    o_inbound_ready
    // Outbound stream
    , output node_message_t                         o_outbound_data
    , output logic                                  o_outbound_valid
    , input  logic                                  i_outbound_ready
);

// Constants
localparam INDEX_WIDTH = $clog2(STREAMS);

// Type definitions
typedef logic [INDEX_WIDTH-1:0] arb_dir_t;

// Arbitrated state
`DECLARE_DQT(node_message_t, arb_data,  i_clk, i_rst, 'd0)
`DECLARE_DQ (             1, arb_valid, i_clk, i_rst, 'd0)
`DECLARE_DQT(     arb_dir_t, arb_next,  i_clk, i_rst, 'd0)

// Connect output
assign o_outbound_data  = arb_data_q;
assign o_outbound_valid = arb_valid_q;

// Detect if outbound stream is stalling
logic outbound_stall;
assign outbound_stall = o_outbound_valid && !i_outbound_ready;

// Round-robin arbitration
arb_dir_t arb_dir;

always_comb begin : comb_arb_select
    int idx;
    logic found;

    // Initialise
    `INIT_D(arb_next);

    // If not stalled, arbitrate next input
    if (!outbound_stall) begin

        // Set the search start point based on the selected arbitration scheme
        case (SCHEME)
            // Round-robin: Start search at the last used input
            nx_primitives::ROUND_ROBIN : arb_next = arb_next_q;
            // Ordinal: Always start the search at zero
            nx_primitives::ORDINAL     : arb_next = 'd0;
        endcase

        // Search for an active stream
        found = 'd0;
        for (idx = 0; idx < STREAMS; idx++) begin
            if (!found) begin
                // Pickup next arbitration
                arb_dir = arb_next;
                // Increment
                arb_next = arb_next + 'd1;
                if ({ 1'b0, arb_next } >= STREAMS) arb_next = 'd0;
                // Check if this stream is active
                found = i_inbound_valid[arb_dir];
            end
        end

    end
end

// Arbitration
assign arb_data  = outbound_stall ? arb_data_q  : i_inbound_data[arb_dir];
assign arb_valid = outbound_stall ? arb_valid_q : i_inbound_valid[arb_dir];

// Drive the ready for the selected stream
generate
for (genvar idx = 0; idx < STREAMS; idx++) begin : gen_dir_ready
    assign o_inbound_ready[idx] = (arb_dir == idx[INDEX_WIDTH-1:0]) && !outbound_stall;
end
endgenerate

endmodule : nx_stream_arbiter
