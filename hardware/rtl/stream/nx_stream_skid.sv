// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

// nx_stream_skid
// Parameterisable stream skid buffer
//
module nx_stream_skid
import NXConstants::*;
(
      input  logic          i_clk
    , input  logic          i_rst
    // Inbound message stream
    , input  node_message_t i_inbound_data
    , input  logic          i_inbound_valid
    , output logic          o_inbound_ready
    // Outbound message stream
    , output node_message_t o_outbound_data
    , output logic          o_outbound_valid
    , input  logic          i_outbound_ready
);

node_message_t buffer_q;
logic          buffer_valid_q;

assign o_outbound_data  = buffer_valid_q ? buffer_q : i_inbound_data;
assign o_outbound_valid = buffer_valid_q || i_inbound_valid;
assign o_inbound_ready  = !buffer_valid_q;

always_ff @(posedge i_clk, posedge i_rst) begin : p_skid
    if (i_rst) begin
        buffer_q       <= 'd0;
        buffer_valid_q <= 'd0;
    end else begin
        // Fill buffer when it is empty and skid is backpressured
        if (!buffer_valid_q && !i_outbound_ready) begin
            buffer_q       <= i_inbound_data;
            buffer_valid_q <= i_inbound_valid;

        // Empty buffer with priority
        end else if (i_outbound_ready) begin
            buffer_valid_q <= 1'b0;

        end
    end
end

endmodule : nx_stream_skid
