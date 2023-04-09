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

// nx_aggregator
// Aggregators sit at the bottom of the mesh and collect the output state,
// reducing the message volume which needs to be sent to the host.
//
module nx_aggregator
import NXConstants::*,
       nx_primitives::ROUND_ROBIN;
#(
      parameter OUTPUTS = 32
) (
      input  logic               i_clk
    , input  logic               i_rst
    // Control signals
    , input  node_id_t           i_node_id
    , output logic               o_idle
    // Output signals
    , output logic [OUTPUTS-1:0] o_outputs
    // Inbound interface from mesh
    , input  node_message_t      i_inbound_data
    , input  logic               i_inbound_valid
    , output logic               o_inbound_ready
    // Passthrough interface from neighbouring aggregator
    , input  node_message_t      i_passthrough_data
    , input  logic               i_passthrough_valid
    , output logic               o_passthrough_ready
    // Outbound interfaces
    , output node_message_t      o_outbound_data
    , output logic               o_outbound_valid
    , input  logic               i_outbound_ready
);

localparam SLOT_W = NXConstants::NODE_MEM_SLOT_WIDTH;
localparam SLOTS  = OUTPUTS / SLOT_W;

// =============================================================================
// Signals & State
// =============================================================================

// Signal message detection
logic is_output;

// Output state
`DECLARE_DQ_ARRAY(SLOT_W, SLOTS, outputs, i_clk, i_rst, 'd0)

// Stream combiner
// NOTE: Not using node_message_t is a workaround for Icarus Verilog
logic [1:0][MESSAGE_WIDTH-1:0] comb_data;
logic [1:0]                    comb_valid, comb_ready;

// =============================================================================
// Detect Signal Messages
// =============================================================================

// Determine if this is an output message (overloaded SIGNAL format)
// NOTE: Only test the column address, not the row, allowing any signals
//       travelling down the column to be captured
assign is_output = (
    (i_inbound_data.aggout.header.target.column == i_node_id.column   ) &&
    (i_inbound_data.aggout.header.command       == NODE_COMMAND_SIGNAL) &&
    (i_inbound_data.aggout.bypass               == 'd0                ) &&
    i_inbound_valid
);

// =============================================================================
// Track Output State
// =============================================================================

// Expose flopped values
generate
for (genvar idx = 0; idx < SLOTS; idx++) begin : gen_expose_outputs
    assign o_outputs[(idx * SLOT_W) +: SLOT_W] = outputs_q[idx];
end
endgenerate

// Capture updated values
generate
for (genvar idx = 0; idx < SLOTS; idx++) begin : gen_capture_outputs
    assign outputs[idx] = (is_output && (idx[$clog2(SLOTS)-1:0] == i_inbound_data.aggout.slot))
                          ? ((i_inbound_data.aggout.data &  i_inbound_data.aggout.mask) |
                             (outputs_q[idx]             & ~i_inbound_data.aggout.mask))
                          : outputs_q[idx];
end
endgenerate

// =============================================================================
// Internal Stream Combiner
// =============================================================================

// Slot 0 comes from the mesh for non-output messages
assign comb_data[0]        = i_inbound_data;
assign comb_valid[0]       = !is_output && i_inbound_valid;
assign o_inbound_ready     = is_output || comb_ready[0];

// Slot 1 comes from the neighbouring aggregator
assign comb_data[1]        = i_passthrough_data;
assign comb_valid[1]       = i_passthrough_valid;
assign o_passthrough_ready = comb_ready[1];

nx_stream_arbiter #(
      .STREAMS          ( 2                )
    , .SCHEME           ( ROUND_ROBIN      )
) u_combiner (
      .i_clk            ( i_clk            )
    , .i_rst            ( i_rst            )
    // Inbound message streams
    , .i_inbound_data   ( comb_data        )
    , .i_inbound_valid  ( comb_valid       )
    , .o_inbound_ready  ( comb_ready       )
    // Outbound stream
    , .o_outbound_data  ( o_outbound_data  )
    , .o_outbound_valid ( o_outbound_valid )
    , .i_outbound_ready ( i_outbound_ready )
);

// =============================================================================
// Determine Idleness
// =============================================================================

assign o_idle = (!i_inbound_valid && !i_passthrough_valid && !o_outbound_valid);

// =============================================================================
// Tie-Off Unused Signals
// =============================================================================

logic _unused;
assign _unused = &{ 1'b0, i_node_id.row };

endmodule : nx_aggregator
