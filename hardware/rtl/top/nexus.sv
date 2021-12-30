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

// nexus
// Top-level of the accelerator.
//
module nexus
import NXConstants::*;
#(
      parameter ROWS       =  3
    , parameter COLUMNS    =  3
    , parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter REGISTERS  = 16
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic              i_clk
    , input  logic              i_rst
    // Status signals
    , output logic              o_status_active
    , output logic              o_status_idle
    , output logic              o_status_trigger
    // Inbound control stream
    , input  control_request_t  i_ctrl_in_data
    , input  logic              i_ctrl_in_valid
    , output logic              o_ctrl_in_ready
    // Outbound control stream
    , output control_response_t o_ctrl_out_data
    , output logic              o_ctrl_out_last
    , output logic              o_ctrl_out_valid
    , input  logic              i_ctrl_out_ready
);

// =============================================================================
// Constants
// =============================================================================

localparam MESH_OUTPUTS = COLUMNS * OUTPUTS;

// =============================================================================
// Internal Signals
// =============================================================================

// Reset stretch
logic rst_soft, rst_internal;

// Mesh controller
node_message_t           mesh_in_data, mesh_out_data;
logic                    mesh_in_valid, mesh_out_valid, mesh_in_ready, mesh_out_ready;
logic [COLUMNS-1:0]      mesh_node_idle, mesh_trigger;
logic                    mesh_agg_idle;
logic [MESH_OUTPUTS-1:0] mesh_outputs;

// =============================================================================
// Reset Stretcher
// =============================================================================

nx_reset u_reset_stretch (
      .i_clk         ( i_clk        )
    , .i_rst_hard    ( i_rst        )
    , .i_rst_soft    ( rst_soft     )
    , .o_rst_internal( rst_internal )
);

// =============================================================================
// Mesh Controller
// =============================================================================

nx_control #(
      .ROWS             ( ROWS             )
    , .COLUMNS          ( COLUMNS          )
    , .INPUTS           ( INPUTS           )
    , .OUTPUTS          ( OUTPUTS          )
    , .REGISTERS        ( REGISTERS        )
) u_control (
      .i_clk            ( i_clk            )
    , .i_rst            ( rst_internal     )
    // Soft reset request
    , .o_soft_reset     ( rst_soft         )
    // Host message streams
    // - Inbound
    , .i_ctrl_in_data   ( i_ctrl_in_data   )
    , .i_ctrl_in_valid  ( i_ctrl_in_valid  )
    , .o_ctrl_in_ready  ( o_ctrl_in_ready  )
    // - Outbound
    , .o_ctrl_out_data  ( o_ctrl_out_data  )
    , .o_ctrl_out_last  ( o_ctrl_out_last  )
    , .o_ctrl_out_valid ( o_ctrl_out_valid )
    , .i_ctrl_out_ready ( i_ctrl_out_ready )
    // Mesh message streams
    // - Inbound
    , .o_mesh_in_data   ( mesh_in_data     )
    , .o_mesh_in_valid  ( mesh_in_valid    )
    , .i_mesh_in_ready  ( mesh_in_ready    )
    // - Outbound
    , .i_mesh_out_data  ( mesh_out_data    )
    , .i_mesh_out_valid ( mesh_out_valid   )
    , .o_mesh_out_ready ( mesh_out_ready   )
    // Externally visible status
    , .o_status_active  ( o_status_active  )
    , .o_status_idle    ( o_status_idle    )
    , .o_status_trigger ( o_status_trigger )
    // Interface to the mesh
    , .i_mesh_node_idle ( mesh_node_idle   )
    , .i_mesh_agg_idle  ( mesh_agg_idle    )
    , .o_mesh_trigger   ( mesh_trigger     )
    , .i_mesh_outputs   ( mesh_outputs     )
);

// =============================================================================
// Mesh
// =============================================================================

nx_mesh #(
      .ROWS             ( ROWS           )
    , .COLUMNS          ( COLUMNS        )
    , .INPUTS           ( INPUTS         )
    , .OUTPUTS          ( OUTPUTS        )
    , .REGISTERS        ( REGISTERS      )
    , .RAM_ADDR_W       ( RAM_ADDR_W     )
    , .RAM_DATA_W       ( RAM_DATA_W     )
) u_mesh (
      .i_clk            ( i_clk          )
    , .i_rst            ( rst_internal   )
    // Control signals
    , .o_node_idle      ( mesh_node_idle )
    , .o_agg_idle       ( mesh_agg_idle  )
    , .i_trigger        ( mesh_trigger   )
    // Inbound stream
    , .i_inbound_data   ( mesh_in_data   )
    , .i_inbound_valid  ( mesh_in_valid  )
    , .o_inbound_ready  ( mesh_in_ready  )
    // Outbound stream
    , .o_outbound_data  ( mesh_out_data  )
    , .o_outbound_valid ( mesh_out_valid )
    , .i_outbound_ready ( mesh_out_ready )
    // Aggregated outputs
    , .o_outputs        ( mesh_outputs   )
);

endmodule : nexus
