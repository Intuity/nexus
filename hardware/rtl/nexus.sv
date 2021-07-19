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

`include "nx_constants.svh"

// nexus
// Top-level of the Nexus simulation accelerator.
//
module nexus #(
      parameter ROWS           =   3
    , parameter COLUMNS        =   3
    , parameter ADDR_ROW_WIDTH =   4
    , parameter ADDR_COL_WIDTH =   4
    , parameter COMMAND_WIDTH  =   2
    , parameter INSTR_WIDTH    =  15
    , parameter INPUTS         =   8
    , parameter OUTPUTS        =   8
    , parameter REGISTERS      =   8
    , parameter MAX_INSTRS     = 512
    , parameter OPCODE_WIDTH   =   3
) (
      input  logic clk_i
    , input  logic rst_i
    // Status signals
    , output logic status_active_o
    , output logic status_idle_o
    , output logic status_trigger_o
    // Control message streams
    // - Inbound
    , input  nx_message_t ctrl_ib_data_i
    , input  logic        ctrl_ib_valid_i
    , output logic        ctrl_ib_ready_o
    // - Outbound
    , output nx_message_t ctrl_ob_data_o
    , output logic        ctrl_ob_valid_o
    , input  logic        ctrl_ob_ready_i
    // Mesh message streams
    // - Inbound
    , input  nx_message_t mesh_ib_data_i
    , input  logic        mesh_ib_valid_i
    , output logic        mesh_ib_ready_o
    // - Outbound
    , output nx_message_t mesh_ob_data_o
    , output logic        mesh_ob_valid_o
    , input  logic        mesh_ob_ready_i
);

// Instance the controller
logic               ctrl_mesh_idle, ctrl_mesh_trigger;
logic [COLUMNS-1:0] ctrl_token_grant, ctrl_token_release;

nx_control #(
      .ROWS     (ROWS     )
    , .COLUMNS  (COLUMNS  )
    , .INPUTS   (INPUTS   )
    , .OUTPUTS  (OUTPUTS  )
    , .REGISTERS(REGISTERS)
) control (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Inbound message stream (from host)
    , .inbound_data_i (ctrl_ib_data_i )
    , .inbound_valid_i(ctrl_ib_valid_i)
    , .inbound_ready_o(ctrl_ib_ready_o)
    // Outbound message stream (to host)
    , .outbound_data_o (ctrl_ob_data_o )
    , .outbound_valid_o(ctrl_ob_valid_o)
    , .outbound_ready_i(ctrl_ob_ready_i)
    // Externally visible status
    , .status_active_o (status_active_o )
    , .status_idle_o   (status_idle_o   )
    , .status_trigger_o(status_trigger_o)
    // Interface to the mesh
    , .mesh_idle_i    (ctrl_mesh_idle    )
    , .mesh_trigger_o (ctrl_mesh_trigger )
    , .token_grant_o  (ctrl_token_grant  )
    , .token_release_i(ctrl_token_release)
);

// Instance the mesh
nx_mesh #(
      .ROWS          (ROWS          )
    , .COLUMNS       (COLUMNS       )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
    , .INSTR_WIDTH   (INSTR_WIDTH   )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
    , .REGISTERS     (REGISTERS     )
    , .MAX_INSTRS    (MAX_INSTRS    )
    , .OPCODE_WIDTH  (OPCODE_WIDTH  )
) mesh (
      .clk_i(clk_i)
    , .rst_i(rst_i)
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