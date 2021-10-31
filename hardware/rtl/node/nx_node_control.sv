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

// nx_node_control
// Controller for each node in the mesh. Handles input state updates, output to
// input loopbacks, output message generation, and triggers logic evaluation.
//
module nx_node_control
import NXConstants::*;
#(
      parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic                        i_clk
    , input  logic                        i_rst
    // Control signals
    , input  logic                        i_trigger
    , output logic                        o_idle
    // Inputs from decoder
    , input  logic [INPUTS-1:0]           i_loopback_mask
    , input  logic [$clog2(INPUTS)-1:0]   i_input_index
    , input  logic                        i_input_value
    , input  logic                        i_input_is_seq
    , input  logic                        i_input_update
    , input  logic [NODE_PARAM_WIDTH-1:0] i_num_instr
    , input  logic [NODE_PARAM_WIDTH-1:0] i_num_output
    // Output message stream
    , output node_message_t               o_msg_data
    , output logic                        o_msg_valid
    , input  logic                        i_msg_ready
    // Interface to store
    , output logic [RAM_ADDR_W-1:0]       o_rd_addr
    , output logic                        o_rd_en
    , input  logic [RAM_DATA_W-1:0]       i_rd_data
    // Interface to logic core
    , output logic [INPUTS-1:0]           o_core_inputs
    , input  logic [OUTPUTS-1:0]          i_core_outputs
    , output logic                        o_core_trigger
);

// =============================================================================
// Internal Signals
// =============================================================================

logic inputs_idle, outputs_idle;

assign o_idle = inputs_idle && outputs_idle;

// =============================================================================
// Input Control
// =============================================================================

nx_node_control_inputs #(
      .INPUTS          ( INPUTS          )
    , .OUTPUTS         ( OUTPUTS         )
) u_inputs (
      .i_clk           ( i_clk           )
    , .i_rst           ( i_rst           )
    // Control signals
    , .i_trigger       ( i_trigger       )
    , .o_idle          ( inputs_idle     )
    // Inputs from decoder
    , .i_loopback_mask ( i_loopback_mask )
    , .i_input_index   ( i_input_index   )
    , .i_input_value   ( i_input_value   )
    , .i_input_is_seq  ( i_input_is_seq  )
    , .i_input_update  ( i_input_update  )
    // Interface to logic core
    , .o_core_inputs   ( o_core_inputs   )
    , .i_core_outputs  ( i_core_outputs  )
    , .o_core_trigger  ( o_core_trigger  )
);

// =============================================================================
// Output Control
// =============================================================================

nx_node_control_outputs #(
      .OUTPUTS        ( OUTPUTS        )
    , .RAM_ADDR_W     ( RAM_ADDR_W     )
    , .RAM_DATA_W     ( RAM_DATA_W     )
) u_outputs (
      .i_clk          ( i_clk          )
    , .i_rst          ( i_rst          )
    // Control signals
    , .o_idle         ( outputs_idle   )
    // Inputs from decoder
    , .i_num_instr    ( i_num_instr    )
    , .i_num_output   ( i_num_output   )
    // Output message stream
    , .o_msg_data     ( o_msg_data     )
    , .o_msg_valid    ( o_msg_valid    )
    , .i_msg_ready    ( i_msg_ready    )
    // Interface to store
    , .o_rd_addr      ( o_rd_addr      )
    , .o_rd_en        ( o_rd_en        )
    , .i_rd_data      ( i_rd_data      )
    // Interface to core
    , .i_core_outputs ( i_core_outputs )
);

endmodule : nx_node_control
