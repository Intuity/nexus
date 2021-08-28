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
) (
      input  wire clk
    , input  wire rstn
    // Status
    , output wire status_active
    , output wire status_idle
    , output wire status_trigger
    // Control AXI4-streams
    // - Inbound
    , input  wire [AXI4_DATA_WIDTH-1:0] inbound_ctrl_tdata
    , input  wire [AXI4_STRB_WIDTH-1:0] inbound_ctrl_tkeep
    , input  wire                       inbound_ctrl_tlast
    , input  wire                       inbound_ctrl_tvalid
    , output wire                       inbound_ctrl_tready
    // - Outbound
    , output wire [AXI4_DATA_WIDTH-1:0] outbound_ctrl_tdata
    , output wire [AXI4_STRB_WIDTH-1:0] outbound_ctrl_tkeep
    , output wire                       outbound_ctrl_tlast
    , output wire                       outbound_ctrl_tvalid
    , input  wire                       outbound_ctrl_tready
    // Mesh AXI4-streams
    // - Inbound
    , input  wire [AXI4_DATA_WIDTH-1:0] inbound_mesh_tdata
    , input  wire [AXI4_STRB_WIDTH-1:0] inbound_mesh_tkeep
    , input  wire                       inbound_mesh_tlast
    , input  wire                       inbound_mesh_tvalid
    , output wire                       inbound_mesh_tready
    // - Outbound
    , output wire [AXI4_DATA_WIDTH-1:0] outbound_mesh_tdata
    , output wire [AXI4_STRB_WIDTH-1:0] outbound_mesh_tkeep
    , output wire                       outbound_mesh_tlast
    , output wire                       outbound_mesh_tvalid
    , input  wire                       outbound_mesh_tready
);

assign outbound_ctrl_tkeep = {AXI4_STRB_WIDTH{1'b1}};
assign outbound_mesh_tkeep = {AXI4_STRB_WIDTH{1'b1}};

// =============================================================================
// AXI4-Stream Bridge for Control
// =============================================================================

wire [30:0] nx_ctrl_ib_data, nx_ctrl_ob_data;
wire        nx_ctrl_ib_valid, nx_ctrl_ib_ready, nx_ctrl_ob_valid, nx_ctrl_ob_ready;

nx_axi4s_bridge #(
    .AXI4_DATA_WIDTH(AXI4_DATA_WIDTH)
) ctrl_bridge (
      .clk_i( clk )
    , .rst_i(~rstn)
    // Inbound AXI4-stream
    , .ib_axi4s_tdata_i (inbound_ctrl_tdata )
    , .ib_axi4s_tlast_i (inbound_ctrl_tlast )
    , .ib_axi4s_tvalid_i(inbound_ctrl_tvalid)
    , .ib_axi4s_tready_o(inbound_ctrl_tready)
    // Outbound Nexus message stream
    , .ob_nx_data_o (nx_ctrl_ib_data )
    , .ob_nx_valid_o(nx_ctrl_ib_valid)
    , .ob_nx_ready_i(nx_ctrl_ib_ready)
    // Inbound Nexus message stream
    , .ib_nx_data_i (nx_ctrl_ob_data )
    , .ib_nx_valid_i(nx_ctrl_ob_valid)
    , .ib_nx_ready_o(nx_ctrl_ob_ready)
    // Outbound AXI4-stream
    , .ob_axi4s_tdata_o (outbound_ctrl_tdata )
    , .ob_axi4s_tlast_o (outbound_ctrl_tlast )
    , .ob_axi4s_tvalid_o(outbound_ctrl_tvalid)
    , .ob_axi4s_tready_i(outbound_ctrl_tready)
);

// =============================================================================
// AXI4-Stream Bridge for Mesh
// =============================================================================

wire [30:0] nx_mesh_ib_data, nx_mesh_ob_data;
wire        nx_mesh_ib_valid, nx_mesh_ib_ready, nx_mesh_ob_valid, nx_mesh_ob_ready;

nx_axi4s_bridge #(
    .AXI4_DATA_WIDTH(AXI4_DATA_WIDTH)
) mesh_bridge (
      .clk_i( clk )
    , .rst_i(~rstn)
    // Inbound AXI4-stream
    , .ib_axi4s_tdata_i (inbound_mesh_tdata )
    , .ib_axi4s_tlast_i (inbound_mesh_tlast )
    , .ib_axi4s_tvalid_i(inbound_mesh_tvalid)
    , .ib_axi4s_tready_o(inbound_mesh_tready)
    // Outbound Nexus message stream
    , .ob_nx_data_o (nx_mesh_ib_data )
    , .ob_nx_valid_o(nx_mesh_ib_valid)
    , .ob_nx_ready_i(nx_mesh_ib_ready)
    // Inbound Nexus message stream
    , .ib_nx_data_i (nx_mesh_ob_data )
    , .ib_nx_valid_i(nx_mesh_ob_valid)
    , .ib_nx_ready_o(nx_mesh_ob_ready)
    // Outbound AXI4-stream
    , .ob_axi4s_tdata_o (outbound_mesh_tdata )
    , .ob_axi4s_tlast_o (outbound_mesh_tlast )
    , .ob_axi4s_tvalid_o(outbound_mesh_tvalid)
    , .ob_axi4s_tready_i(outbound_mesh_tready)
);

// =============================================================================
// Nexus Instance
// =============================================================================

nexus #(
      .ROWS          (  6)
    , .COLUMNS       (  6)
    , .ADDR_ROW_WIDTH(  4)
    , .ADDR_COL_WIDTH(  4)
    , .INSTR_WIDTH   ( 21)
    , .INPUTS        ( 32)
    , .OUTPUTS       ( 32)
    , .REGISTERS     (  8)
    , .MAX_INSTRS    (512)
    , .OPCODE_WIDTH  (  3)
) core (
      .clk_i( clk )
    , .rst_i(~rstn)
    // Status signals
    , .status_active_o (status_active )
    , .status_idle_o   (status_idle   )
    , .status_trigger_o(status_trigger)
    // Control message streams
    // - Inbound
    , .ctrl_ib_data_i (nx_ctrl_ib_data )
    , .ctrl_ib_valid_i(nx_ctrl_ib_valid)
    , .ctrl_ib_ready_o(nx_ctrl_ib_ready)
    // - Outbound
    , .ctrl_ob_data_o (nx_ctrl_ob_data )
    , .ctrl_ob_valid_o(nx_ctrl_ob_valid)
    , .ctrl_ob_ready_i(nx_ctrl_ob_ready)
    // Mesh message streams
    // - Inbound
    , .mesh_ib_data_i (nx_mesh_ib_data )
    , .mesh_ib_valid_i(nx_mesh_ib_valid)
    , .mesh_ib_ready_o(nx_mesh_ib_ready)
    // - Outbound
    , .mesh_ob_data_o (nx_mesh_ob_data )
    , .mesh_ob_valid_o(nx_mesh_ob_valid)
    , .mesh_ob_ready_i(nx_mesh_ob_ready)
);

endmodule : nx_artix_200t
