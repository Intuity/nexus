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

// nx_node_decoder
// A single node with messages interfaces in each cardinal direction
//
module nx_node_decoder
import NXConstants::*,
       nx_primitives::ROUND_ROBIN;
#(
      localparam RAM_ADDR_W = 10
    , localparam RAM_DATA_W = 32
    , localparam RAM_STRB_W =  4
) (
      input  logic                          i_clk
    , input  logic                          i_rst
    // Control signals
    , input  node_id_t                      i_node_id
    , output logic                          o_idle
    // Inbound interfaces
    , input  logic [3:0][MESSAGE_WIDTH-1:0] i_inbound_data
    , input  logic [3:0]                    i_inbound_valid
    , output logic [3:0]                    o_inbound_ready
    // Bypass interface
    , input  node_message_t                 o_bypass_data
    , input  logic                          o_bypass_valid
    , output logic                          i_bypass_ready
    // Instruction RAM
    , output logic [RAM_ADDR_W-1:0]         o_inst_addr
    , output logic [RAM_DATA_W-1:0]         o_inst_wr_data
    , output logic [RAM_STRB_W-1:0]         o_inst_wr_strb
    // Data RAM
    , output logic [RAM_ADDR_W-1:0]         o_data_addr
    , output logic [RAM_DATA_W-1:0]         o_data_wr_data
    , output logic [RAM_STRB_W-1:0]         o_data_wr_strb
);

// =============================================================================
// Signals
// =============================================================================

// Inbound stream arbiter
node_message_t arb_data;
logic          arb_valid, arb_ready, arb_match;

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
    (arb_data.raw.header.row    == i_node_id.row   ) &&
    (arb_data.raw.header.column == i_node_id.column)
);

endmodule : nx_node_decoder
