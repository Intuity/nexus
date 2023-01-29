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

// nx_node_decoder
// A single node with messages interfaces in each cardinal direction
//
module nx_node_decoder
import NXConstants::*,
       nx_primitives::ROUND_ROBIN;
#(
      localparam RAM_ADDR_W = 10
    , localparam RAM_DATA_W = 32
) (
      input  logic                          i_clk
    , input  logic                          i_rst
    // Control signals
    , input  node_id_t                      i_node_id
    , output logic                          o_idle
    , input  logic                          i_slot
    // Inbound interfaces
    , input  logic [3:0][MESSAGE_WIDTH-1:0] i_inbound_data
    , input  logic [3:0]                    i_inbound_valid
    , output logic [3:0]                    o_inbound_ready
    // Bypass interface
    , output node_message_t                 o_bypass_data
    , output logic                          o_bypass_valid
    , input  logic                          i_bypass_ready
    // Instruction RAM
    , output logic [RAM_ADDR_W-1:0]         o_inst_addr
    , output logic [RAM_DATA_W-1:0]         o_inst_wr_data
    , output logic [RAM_DATA_W-1:0]         o_inst_wr_strb
    // Data RAM
    , output logic [RAM_ADDR_W-1:0]         o_data_addr
    , output logic [RAM_DATA_W-1:0]         o_data_wr_data
    , output logic [RAM_DATA_W-1:0]         o_data_wr_strb
);

// =============================================================================
// Signals
// =============================================================================

// Inbound stream arbiter
node_message_t arb_data;
logic          arb_valid, arb_ready, arb_match;

// Decode
logic is_msg_load, is_msg_signal;

// =============================================================================
// Idle
// =============================================================================

assign o_idle = !(|i_inbound_valid);

// =============================================================================
// Inbound Arbiter
// =============================================================================

nx_stream_arbiter #(
      .STREAMS          ( 4               )
    , .SCHEME           ( ROUND_ROBIN     )
) u_arbiter (
      .i_clk            ( i_clk           )
    , .i_rst            ( i_rst           )
    // Inbound message streams
    , .i_inbound_data   ( i_inbound_data  )
    , .i_inbound_valid  ( i_inbound_valid )
    , .o_inbound_ready  ( o_inbound_ready )
    // Outbound stream
    , .o_outbound_data  ( arb_data        )
    , .o_outbound_valid ( arb_valid       )
    , .i_outbound_ready ( arb_ready       )
);

// Detect if the arbitrated stream targets this node
assign arb_match = (
    (arb_data.raw.header.target.row    == i_node_id.row   ) &&
    (arb_data.raw.header.target.column == i_node_id.column)
);

// Qualify bypass if not matched
assign o_bypass_data   = arb_data;
assign o_bypass_valid  = arb_valid && !arb_match;
assign arb_ready       = arb_match || i_bypass_ready;

// =============================================================================
// Decoding
// =============================================================================

// Detect the type of message
assign is_msg_load   = arb_match && (arb_data.raw.header.command == NODE_COMMAND_LOAD  );
assign is_msg_signal = arb_match && (arb_data.raw.header.command == NODE_COMMAND_SIGNAL);

// Instruction RAM interface
assign o_inst_addr    = arb_data.load.address[10:1];
assign o_inst_wr_data = {4{arb_data.load.data}};
assign o_inst_wr_strb = (
    {24'd0, {8{is_msg_load}}} << {arb_data.load.address[0], arb_data.load.slot, 3'd0}
);

// Data RAM interface
assign o_data_addr    = arb_data.signal.address[10:1];
assign o_data_wr_data = {4{arb_data.signal.data}};

always_comb begin : comb_data_slot
    logic slot;
    case (arb_data.signal.slot)
        MEMORY_SLOT_PRESERVE: slot =  i_slot;
        MEMORY_SLOT_INVERSE : slot = ~i_slot;
        MEMORY_SLOT_UPPER   : slot = 1'b1;
        MEMORY_SLOT_LOWER   : slot = 1'b0;
    endcase
    o_data_wr_strb = {24'd0, {8{is_msg_signal}}} << {arb_data.signal.address[0], slot, 3'd0};
end

endmodule : nx_node_decoder
