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

module testbench
import NXConstants::*;
#(
      parameter ROWS      =  3
    , parameter COLUMNS   = 10
    , parameter INPUTS    = 32
    , parameter OUTPUTS   = 32
    , parameter REGISTERS = 16
) (
      input  logic                         rst
    // Soft reset request
    , output logic                         o_soft_reset
    // Host message streams
    // - Inbound
    , input  control_request_t             i_ctrl_in_data
    , input  logic                         i_ctrl_in_valid
    , output logic                         o_ctrl_in_ready
    // - Outbound
    , output control_response_t            o_ctrl_out_data
    , output logic                         o_ctrl_out_valid
    , input  logic                         i_ctrl_out_ready
    // Mesh message streams
    // - Inbound
    , output node_message_t                o_mesh_in_data
    , output logic                         o_mesh_in_valid
    , input  logic                         i_mesh_in_ready
    // - Outbound
    , input  node_message_t                i_mesh_out_data
    , input  logic                         i_mesh_out_valid
    , output logic                         o_mesh_out_ready
    // Externally visible status
    , output logic                         o_status_active
    , output logic                         o_status_idle
    , output logic                         o_status_trigger
    // Interface to the mesh
    , input  logic [COLUMNS-1:0]           i_mesh_node_idle
    , input  logic                         i_mesh_agg_idle
    , output logic [COLUMNS-1:0]           o_mesh_trigger
    , input  logic [(COLUMNS*OUTPUTS)-1:0] i_mesh_outputs
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// DUT Instance
// =============================================================================

nx_control #(
      .ROWS             ( ROWS             )
    , .COLUMNS          ( COLUMNS          )
    , .INPUTS           ( INPUTS           )
    , .OUTPUTS          ( OUTPUTS          )
    , .REGISTERS        ( REGISTERS        )
) u_dut (
      .i_clk            ( clk              )
    , .i_rst            ( rst              )
    // Soft reset request
    , .o_soft_reset     ( o_soft_reset     )
    // Host message streams
    // - Inbound
    , .i_ctrl_in_data   ( i_ctrl_in_data   )
    , .i_ctrl_in_valid  ( i_ctrl_in_valid  )
    , .o_ctrl_in_ready  ( o_ctrl_in_ready  )
    // - Outbound
    , .o_ctrl_out_data  ( o_ctrl_out_data  )
    , .o_ctrl_out_valid ( o_ctrl_out_valid )
    , .i_ctrl_out_ready ( i_ctrl_out_ready )
    // Mesh message streams
    // - Inbound
    , .o_mesh_in_data   ( o_mesh_in_data   )
    , .o_mesh_in_valid  ( o_mesh_in_valid  )
    , .i_mesh_in_ready  ( i_mesh_in_ready  )
    // - Outbound
    , .i_mesh_out_data  ( i_mesh_out_data  )
    , .i_mesh_out_valid ( i_mesh_out_valid )
    , .o_mesh_out_ready ( o_mesh_out_ready )
    // Externally visible status
    , .o_status_active  ( o_status_active  )
    , .o_status_idle    ( o_status_idle    )
    , .o_status_trigger ( o_status_trigger )
    // Interface to the mesh
    , .i_mesh_node_idle ( i_mesh_node_idle )
    , .i_mesh_agg_idle  ( i_mesh_agg_idle  )
    , .o_mesh_trigger   ( o_mesh_trigger   )
    , .i_mesh_outputs   ( i_mesh_outputs   )
);

// =============================================================================
// Tracing
// =============================================================================

`ifdef sim_icarus
initial begin : i_trace
    string f_name;
    $timeformat(-9, 2, " ns", 20);
    if ($value$plusargs("WAVE_FILE=%s", f_name)) begin
        $display("%0t: Capturing wave file %s", $time, f_name);
        $dumpfile(f_name);
        $dumpvars(0, testbench);
    end else begin
        $display("%0t: No filename provided - disabling wave capture", $time);
    end
end
`endif // sim_icarus

endmodule : testbench
