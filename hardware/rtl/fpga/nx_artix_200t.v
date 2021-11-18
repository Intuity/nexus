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
    // Control AXI4-streams
    // - Inbound
    , input  wire [AXI4_DATA_WIDTH-1:0] inbound_ctrl_tdata
    , input  wire                       inbound_ctrl_tlast
    , input  wire                       inbound_ctrl_tvalid
    , output wire                       inbound_ctrl_tready
    // - Outbound
    , output wire [AXI4_DATA_WIDTH-1:0] outbound_ctrl_tdata
    , output wire                       outbound_ctrl_tlast
    , output wire                       outbound_ctrl_tvalid
    , input  wire                       outbound_ctrl_tready
    // Mesh AXI4-streams
    // - Inbound
    , input  wire [AXI4_DATA_WIDTH-1:0] inbound_mesh_tdata
    , input  wire                       inbound_mesh_tlast
    , input  wire                       inbound_mesh_tvalid
    , output wire                       inbound_mesh_tready
    // - Outbound
    , output wire [AXI4_DATA_WIDTH-1:0] outbound_mesh_tdata
    , output wire                       outbound_mesh_tlast
    , output wire                       outbound_mesh_tvalid
    , input  wire                       outbound_mesh_tready
);

// =============================================================================
// AXI4-Stream Bridge for Control
// =============================================================================

wire [26:0] nx_ctrl_ib_data, nx_ctrl_ob_data;
wire        nx_ctrl_ib_valid, nx_ctrl_ib_ready, nx_ctrl_ob_valid, nx_ctrl_ob_ready;

nx_axi4s_bridge #(
      .AXI4_DATA_WIDTH   ( AXI4_DATA_WIDTH      )
) u_ctrl_bridge (
      .i_clk             (  clk                 )
    , .i_rst             ( ~rstn                )
    // Inbound AXI4-stream
    , .i_ib_axi4s_tdata  ( inbound_ctrl_tdata   )
    , .i_ib_axi4s_tlast  ( inbound_ctrl_tlast   )
    , .i_ib_axi4s_tvalid ( inbound_ctrl_tvalid  )
    , .o_ib_axi4s_tready ( inbound_ctrl_tready  )
    // Outbound Nexus message stream
    , .o_ob_nx_data      ( nx_ctrl_ib_data      )
    , .o_ob_nx_valid     ( nx_ctrl_ib_valid     )
    , .i_ob_nx_ready     ( nx_ctrl_ib_ready     )
    // Inbound Nexus message stream
    , .i_ib_nx_data      ( nx_ctrl_ob_data      )
    , .i_ib_nx_valid     ( nx_ctrl_ob_valid     )
    , .o_ib_nx_ready     ( nx_ctrl_ob_ready     )
    // Outbound AXI4-stream
    , .o_ob_axi4s_tdata  ( outbound_ctrl_tdata  )
    , .o_ob_axi4s_tlast  ( outbound_ctrl_tlast  )
    , .o_ob_axi4s_tvalid ( outbound_ctrl_tvalid )
    , .i_ob_axi4s_tready ( outbound_ctrl_tready )
);

// =============================================================================
// AXI4-Stream Bridge for Mesh
// =============================================================================

wire [26:0] nx_mesh_ib_data, nx_mesh_ob_data;
wire        nx_mesh_ib_valid, nx_mesh_ib_ready, nx_mesh_ob_valid, nx_mesh_ob_ready;

nx_axi4s_bridge #(
      .AXI4_DATA_WIDTH   ( AXI4_DATA_WIDTH      )
) u_mesh_bridge (
      .i_clk             (  clk                 )
    , .i_rst             ( ~rstn                )
    // Inbound AXI4-stream
    , .i_ib_axi4s_tdata  ( inbound_mesh_tdata   )
    , .i_ib_axi4s_tlast  ( inbound_mesh_tlast   )
    , .i_ib_axi4s_tvalid ( inbound_mesh_tvalid  )
    , .o_ib_axi4s_tready ( inbound_mesh_tready  )
    // Outbound Nexus message stream
    , .o_ob_nx_data      ( nx_mesh_ib_data      )
    , .o_ob_nx_valid     ( nx_mesh_ib_valid     )
    , .i_ob_nx_ready     ( nx_mesh_ib_ready     )
    // Inbound Nexus message stream
    , .i_ib_nx_data      ( nx_mesh_ob_data      )
    , .i_ib_nx_valid     ( nx_mesh_ob_valid     )
    , .o_ib_nx_ready     ( nx_mesh_ob_ready     )
    // Outbound AXI4-stream
    , .o_ob_axi4s_tdata  ( outbound_mesh_tdata  )
    , .o_ob_axi4s_tlast  ( outbound_mesh_tlast  )
    , .o_ob_axi4s_tvalid ( outbound_mesh_tvalid )
    , .i_ob_axi4s_tready ( outbound_mesh_tready )
);

// =============================================================================
// Nexus Instance
// =============================================================================

nexus #(
      .ROWS             ( ROWS             )
    , .COLUMNS          ( COLUMNS          )
    , .INPUTS           ( 32               )
    , .OUTPUTS          ( 32               )
    , .REGISTERS        ( 16               )
    , .RAM_ADDR_W       ( 10               )
    , .RAM_DATA_W       ( 32               )
) u_nexus (
      .i_clk            ( clk              )
    , .i_rst            ( ~rstn            )
    // Status signals
    , .o_status_active  ( status_active    )
    , .o_status_idle    ( status_idle      )
    , .o_status_trigger ( status_trigger   )
    // Control message streams
    // - Inbound
    , .i_ctrl_ib_data   ( nx_ctrl_ib_data  )
    , .i_ctrl_ib_valid  ( nx_ctrl_ib_valid )
    , .o_ctrl_ib_ready  ( nx_ctrl_ib_ready )
    // - Outbound
    , .o_ctrl_ob_data   ( nx_ctrl_ob_data  )
    , .o_ctrl_ob_valid  ( nx_ctrl_ob_valid )
    , .i_ctrl_ob_ready  ( nx_ctrl_ob_ready )
    // Mesh message streams
    // - Inbound
    , .i_mesh_ib_data   ( nx_mesh_ib_data  )
    , .i_mesh_ib_valid  ( nx_mesh_ib_valid )
    , .o_mesh_ib_ready  ( nx_mesh_ib_ready )
    // - Outbound
    , .o_mesh_ob_data   ( nx_mesh_ob_data  )
    , .o_mesh_ob_valid  ( nx_mesh_ob_valid )
    , .i_mesh_ob_ready  ( nx_mesh_ob_ready )
);

endmodule : nx_artix_200t
