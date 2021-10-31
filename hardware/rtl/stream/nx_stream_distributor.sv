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
#(
      parameter STREAMS = 4
) (
      input  logic                                  i_clk
    , input  logic                                  i_rst
    // Idle flag
    , output logic                                  o_idle
    // Inbound message stream
    , input  logic [$clog2(STREAMS)-1:0]            i_inbound_target
    , input  node_message_t                         i_inbound_data
    , input  logic                                  i_inbound_valid
    , output logic                                  o_inbound_ready
    // Outbound message streams
    , output logic [STREAMS-1:0][MESSAGE_WIDTH-1:0] o_outbound_data
    , output logic [STREAMS-1:0]                    o_outbound_valid
    , input  logic [STREAMS-1:0]                    i_outbound_ready
);

// Constants
localparam STREAM_WIDTH = $clog2(STREAMS);

// Outbound FIFOs
logic [STREAMS-1:0] fifo_full, fifo_empty;

generate
for (genvar idx = 0; idx < STREAMS; idx++) begin : gen_egress_fifo
    logic fifo_match, fifo_push, fifo_pop;

    assign fifo_match = (i_inbound_target == idx[STREAM_WIDTH-1:0]);
    assign fifo_push  = fifo_match && i_inbound_valid && !fifo_full[idx];
    assign fifo_pop   = !fifo_empty[idx] && i_outbound_ready[idx];

    assign o_outbound_valid[idx] = !fifo_empty[idx];

    nx_fifo #(
          .DEPTH     ( 2                     )
        , .WIDTH     ( $bits(node_message_t) )
    ) egress_fifo (
          .i_clk     ( i_clk                 )
        , .i_rst     ( i_rst                 )
        // Write interface
        , .i_wr_data ( i_inbound_data        )
        , .i_wr_push ( fifo_push             )
        // Read interface
        , .o_rd_data ( o_outbound_data[idx]  )
        , .i_rd_pop  ( fifo_pop              )
        // Status
        , .o_level   (                       )
        , .o_empty   ( fifo_empty[idx]       )
        , .o_full    ( fifo_full[idx]        )
    );
end
endgenerate

// Drive inbound stream ready
assign o_inbound_ready = !fifo_full[i_inbound_target];

// Detect idleness
assign o_idle = (&fifo_empty) && !i_inbound_valid;

endmodule : nx_stream_distributor
