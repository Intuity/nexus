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
// Top-level of the Nexus simulation accelerator.
//
module nexus
import NXConstants::*;
#(
      parameter ROWS       = 3
    , parameter COLUMNS    = 3
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
    // Control message streams
    // - Inbound
    , input  control_message_t  i_ctrl_ib_data
    , input  logic              i_ctrl_ib_valid
    , output logic              o_ctrl_ib_ready
    // - Outbound
    , output control_response_t o_ctrl_ob_data
    , output logic              o_ctrl_ob_valid
    , input  logic              i_ctrl_ob_ready
    // Mesh message streams
    // - Inbound
    , input  node_message_t     i_mesh_ib_data
    , input  logic              i_mesh_ib_valid
    , output logic              o_mesh_ib_ready
    // - Outbound
    , output node_message_t     o_mesh_ob_data
    , output logic              o_mesh_ob_valid
    , input  logic              i_mesh_ob_ready
);

// =============================================================================
// Internal Signals
// =============================================================================

// Reset stretch
logic rst_soft, rst_internal;

// Mesh controller
logic [COLUMNS-1:0] ctrl_mesh_idle, ctrl_trigger;

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
    // Inbound message stream (from host)
    , .i_inbound_data   ( i_ctrl_ib_data   )
    , .i_inbound_valid  ( i_ctrl_ib_valid  )
    , .o_inbound_ready  ( o_ctrl_ib_ready  )
    // Outbound message stream (to host)
    , .o_outbound_data  ( o_ctrl_ob_data   )
    , .o_outbound_valid ( o_ctrl_ob_valid  )
    , .i_outbound_ready ( i_ctrl_ob_ready  )
    // Soft reset request
    , .o_soft_reset     ( rst_soft         )
    // Externally visible status
    , .o_status_active  ( o_status_active  )
    , .o_status_idle    ( o_status_idle    )
    , .o_status_trigger ( o_status_trigger )
    // Interface to the mesh
    , .i_mesh_idle      ( ctrl_mesh_idle   )
    , .o_mesh_trigger   ( ctrl_trigger     )
);

// =============================================================================
// Mesh
// =============================================================================

nx_mesh #(
      .ROWS             ( ROWS            )
    , .COLUMNS          ( COLUMNS         )
    , .INPUTS           ( INPUTS          )
    , .OUTPUTS          ( OUTPUTS         )
    , .REGISTERS        ( REGISTERS       )
    , .RAM_ADDR_W       ( RAM_ADDR_W      )
    , .RAM_DATA_W       ( RAM_DATA_W      )
) u_mesh (
      .i_clk            ( i_clk           )
    , .i_rst            ( rst_internal    )
    // Control signals
    , .o_idle           ( ctrl_mesh_idle  )
    , .i_trigger        ( ctrl_trigger    )
    // Inbound stream
    , .i_inbound_data   ( i_mesh_ib_data  )
    , .i_inbound_valid  ( i_mesh_ib_valid )
    , .o_inbound_ready  ( o_mesh_ib_ready )
    // Outbound stream
    , .o_outbound_data  ( o_mesh_ob_data  )
    , .o_outbound_valid ( o_mesh_ob_valid )
    , .i_outbound_ready ( i_mesh_ob_ready )
);

endmodule : nexus
