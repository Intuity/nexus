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

// nx_artix_200t
// Nexus 7 instance for the Artix-7 XC7A200T
//
module nx_artix_200t #(
      parameter AXI4_DATA_WIDTH = 128
    , parameter AXI4_STRB_WIDTH = AXI4_DATA_WIDTH / 8
    , parameter ROWS            =  10
    , parameter COLUMNS         =  10
) (
      input  wire                       clk
    , input  wire                       rstn
    // Status
    , output wire                       status_active
    , output wire                       status_idle
    , output wire                       status_trigger
    // Inbound AXI4-stream
    , input  wire [AXI4_DATA_WIDTH-1:0] inbound_tdata
    , input  wire                       inbound_tlast
    , input  wire                       inbound_tvalid
    , output wire                       inbound_tready
    // Outbound AXI4-stream
    , output wire [AXI4_DATA_WIDTH-1:0] outbound_tdata
    , output wire                       outbound_tlast
    , output wire                       outbound_tvalid
    , input  wire                       outbound_tready
);

// =============================================================================
// Nexus Instance
// =============================================================================

wire                       rst_internal;
wire [AXI4_DATA_WIDTH-1:0] ctrl_out_data;
wire                       ctrl_out_last, ctrl_out_valid, ctrl_out_ready;

nexus #(
      .ROWS             ( ROWS           )
    , .COLUMNS          ( COLUMNS        )
) u_nexus (
      .i_clk            ( clk            )
    , .i_rst            ( ~rstn          )
    , .o_rst_internal   ( rst_internal   )
    // Status signals
    , .o_status_active  ( status_active  )
    , .o_status_idle    ( status_idle    )
    , .o_status_trigger ( status_trigger )
    // Inbound control stream
    , .i_ctrl_in_data   ( inbound_tdata  )
    , .i_ctrl_in_valid  ( inbound_tvalid )
    , .o_ctrl_in_ready  ( inbound_tready )
    // Outbound control stream
    , .o_ctrl_out_data  ( ctrl_out_data  )
    , .o_ctrl_out_last  ( ctrl_out_last  )
    , .o_ctrl_out_valid ( ctrl_out_valid )
    , .i_ctrl_out_ready ( ctrl_out_ready )
);

// =============================================================================
// Outbound Stream Padding
// =============================================================================

nx_control_padder u_padder (
      .i_clk            ( clk             )
    , .i_rst            ( rst_internal    )
    // Inbound stream
    , .i_inbound_data   ( ctrl_out_data   )
    , .i_inbound_last   ( ctrl_out_last   )
    , .i_inbound_valid  ( ctrl_out_valid  )
    , .o_inbound_ready  ( ctrl_out_ready  )
    // Outbound stream
    , .o_outbound_data  ( outbound_tdata  )
    , .o_outbound_last  ( outbound_tlast  )
    , .o_outbound_valid ( outbound_tvalid )
    , .i_outbound_ready ( outbound_tready )
);

// =============================================================================
// Tie-Offs
// =============================================================================

wire _unused;
assign _unused = &{ 1'b0, inbound_tlast };

endmodule : nx_artix_200t
