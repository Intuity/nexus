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
      parameter ROWS      =  3
    , parameter COLUMNS   =  3
    , parameter INPUTS    = 32
    , parameter OUTPUTS   = 32
    , parameter REGISTERS =  8
) (
      input  logic clk_i
    , input  logic rst_i
    // Status signals
    , output logic status_active_o
    , output logic status_idle_o
    , output logic status_trigger_o
    // Control message streams
    // - Inbound
    , input  control_message_t ctrl_ib_data_i
    , input  logic             ctrl_ib_valid_i
    , output logic             ctrl_ib_ready_o
    // - Outbound
    , output control_response_t ctrl_ob_data_o
    , output logic              ctrl_ob_valid_o
    , input  logic              ctrl_ob_ready_i
    // Mesh message streams
    // - Inbound
    , input  node_message_t mesh_ib_data_i
    , input  logic          mesh_ib_valid_i
    , output logic          mesh_ib_ready_o
    // - Outbound
    , output node_message_t mesh_ob_data_o
    , output logic          mesh_ob_valid_o
    , input  logic          mesh_ob_ready_i
);

// Instance the reset stretcher
logic rst_soft, rst_internal;

nx_reset reset_stretch (
      .clk_i         (clk_i       )
    , .rst_hard_i    (rst_i       )
    , .rst_soft_i    (rst_soft    )
    , .rst_internal_o(rst_internal)
);

// Instance the controller
logic               ctrl_mesh_idle, ctrl_trigger;
logic [COLUMNS-1:0] ctrl_token_grant, ctrl_token_release;

nx_control #(
      .ROWS     (ROWS     )
    , .COLUMNS  (COLUMNS  )
    , .INPUTS   (INPUTS   )
    , .OUTPUTS  (OUTPUTS  )
    , .REGISTERS(REGISTERS)
) control (
      .clk_i(clk_i       )
    , .rst_i(rst_internal)
    // Inbound message stream (from host)
    , .inbound_data_i (ctrl_ib_data_i )
    , .inbound_valid_i(ctrl_ib_valid_i)
    , .inbound_ready_o(ctrl_ib_ready_o)
    // Outbound message stream (to host)
    , .outbound_data_o (ctrl_ob_data_o )
    , .outbound_valid_o(ctrl_ob_valid_o)
    , .outbound_ready_i(ctrl_ob_ready_i)
    // Soft reset request
    , .soft_reset_o(rst_soft)
    // Externally visible status
    , .status_active_o (status_active_o )
    , .status_idle_o   (status_idle_o   )
    , .status_trigger_o(status_trigger_o)
    // Interface to the mesh
    , .mesh_idle_i    (ctrl_mesh_idle    )
    , .mesh_trigger_o (ctrl_trigger      )
    , .token_grant_o  (ctrl_token_grant  )
    , .token_release_i(ctrl_token_release)
);

// Instance the mesh
nx_mesh #(
      .ROWS     (ROWS     )
    , .COLUMNS  (COLUMNS  )
    , .INPUTS   (INPUTS   )
    , .OUTPUTS  (OUTPUTS  )
    , .REGISTERS(REGISTERS)
) mesh (
      .clk_i(clk_i       )
    , .rst_i(rst_internal)
    // Control signals
    , .idle_o   (ctrl_mesh_idle)
    , .trigger_i(ctrl_trigger  )
    // Token signals
    , .token_grant_i  (ctrl_token_grant  )
    , .token_release_o(ctrl_token_release)
    // Inbound stream
    , .inbound_data_i (mesh_ib_data_i )
    , .inbound_valid_i(mesh_ib_valid_i)
    , .inbound_ready_o(mesh_ib_ready_o)
    // Outbound stream
    , .outbound_data_o (mesh_ob_data_o )
    , .outbound_valid_o(mesh_ob_valid_o)
    , .outbound_ready_i(mesh_ob_ready_i)
);

endmodule : nexus
