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

// nx_control_padder
// Pads the control stream to deliver fixed sized packets to the host. If the
// stream terminates (by raising LAST) before a whole packet is emitted, then
// a padding response will be injected.
//
module nx_control_padder
import NXConstants::*;
(
      input  logic              i_clk
    , input  logic              i_rst
    // Inbound stream
    , input  control_response_t i_inbound_data
    , input  logic              i_inbound_last
    , input  logic              i_inbound_valid
    , output logic              o_inbound_ready
    // Outbound stream
    , output control_response_t o_outbound_data
    , output logic              o_outbound_last
    , output logic              o_outbound_valid
    , input  logic              i_outbound_ready
);

// =============================================================================
// Constants
// =============================================================================

localparam SLOT_COUNT_W = $clog2(SLOTS_PER_PACKET);

// =============================================================================
// Signals and State
// =============================================================================

// Packet level counting
`DECLARE_DQ(SLOT_COUNT_W, level, i_clk, i_rst, 'd0)

// Inbound stream
logic inbound_last;

// Padding generation
`DECLARE_DQ(1, pad_stream, i_clk, i_rst, 'd0)

control_response_padding_t padding_data;

// Outbound stream
`DECLARE_DQ(CONTROL_WIDTH, outbound_data,  i_clk, i_rst, 'd0)
`DECLARE_DQ(            1, outbound_last,  i_clk, i_rst, 'd0)
`DECLARE_DQ(            1, outbound_valid, i_clk, i_rst, 'd0)

logic outbound_stall;

// =============================================================================
// Inbound Stream
// =============================================================================

// Detect last tick of inbound data
assign inbound_last = i_inbound_valid && i_inbound_last && o_inbound_ready;

// Apply backpressure to the inbound stream
assign o_inbound_ready = !outbound_stall && !pad_stream_q;

// =============================================================================
// Padding Generation
// =============================================================================

// Determine when padding should be activated
assign pad_stream = (
    (pad_stream_q || inbound_last) && (
        outbound_stall || (level_q != (SLOTS_PER_PACKET - 'd1))
    )
);

// Construct the padding packet
assign padding_data.format     = CONTROL_RESP_TYPE_PADDING;
assign padding_data.entries    = SLOTS_PER_PACKET - level_q;
assign padding_data._padding_0 = 'd0;

// =============================================================================
// Outbound Stream
// =============================================================================

// Detect a stall on the outbound stream
assign outbound_stall = outbound_valid_q && !i_outbound_ready;

// Mux the outbound data
assign outbound_data = outbound_stall ? outbound_data_q :
                       pad_stream_q   ? padding_data
                                      : i_inbound_data;

// Determine outbound last
assign outbound_last = outbound_stall ? outbound_last_q
                                      : (level_q == (SLOTS_PER_PACKET - 1));

// Determine outbound valid
assign outbound_valid = outbound_stall || pad_stream_q || i_inbound_valid;

// Increment level counter on every send
assign level = level_q + ((outbound_valid && !outbound_stall) ? 'd1 : 'd0);

// Link to the interface
assign o_outbound_data  = outbound_data_q;
assign o_outbound_last  = outbound_last_q;
assign o_outbound_valid = outbound_valid_q;

endmodule : nx_control_padder
