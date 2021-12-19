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

module testbench #(
      parameter AXI4_DATA_WIDTH = 128
    , parameter ROWS            =   3
    , parameter COLUMNS         =   3
) (
      input  wire                       rst
    // Status
    , output wire                       o_status_active
    , output wire                       o_status_idle
    , output wire                       o_status_trigger
    // Control AXI4-streams
    // - Inbound
    , input  wire [AXI4_DATA_WIDTH-1:0] i_inbound_ctrl_tdata
    , input  wire                       i_inbound_ctrl_tlast
    , input  wire                       i_inbound_ctrl_tvalid
    , output wire                       o_inbound_ctrl_tready
    // - Outbound
    , output wire [AXI4_DATA_WIDTH-1:0] o_outbound_ctrl_tdata
    , output wire                       o_outbound_ctrl_tlast
    , output wire                       o_outbound_ctrl_tvalid
    , input  wire                       i_outbound_ctrl_tready
    // Mesh AXI4-streams
    // - Inbound
    , input  wire [AXI4_DATA_WIDTH-1:0] i_inbound_mesh_tdata
    , input  wire                       i_inbound_mesh_tlast
    , input  wire                       i_inbound_mesh_tvalid
    , output wire                       o_inbound_mesh_tready
    // - Outbound
    , output wire [AXI4_DATA_WIDTH-1:0] o_outbound_mesh_tdata
    , output wire                       o_outbound_mesh_tlast
    , output wire                       o_outbound_mesh_tvalid
    , input  wire                       i_outbound_mesh_tready
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// DUT Instance
// =============================================================================

nx_artix_200t #(
      .AXI4_DATA_WIDTH      ( AXI4_DATA_WIDTH        )
    , .ROWS                 ( ROWS                   )
    , .COLUMNS              ( COLUMNS                )
) u_dut (
      .clk                  (  clk                   )
    , .rstn                 ( ~rst                   )
    // Status
    , .status_active        ( o_status_active        )
    , .status_idle          ( o_status_idle          )
    , .status_trigger       ( o_status_trigger       )
    // Control AXI4-streams
    // - Inbound
    , .inbound_ctrl_tdata   ( i_inbound_ctrl_tdata   )
    , .inbound_ctrl_tlast   ( i_inbound_ctrl_tlast   )
    , .inbound_ctrl_tvalid  ( i_inbound_ctrl_tvalid  )
    , .inbound_ctrl_tready  ( o_inbound_ctrl_tready  )
    // - Outbound
    , .outbound_ctrl_tdata  ( o_outbound_ctrl_tdata  )
    , .outbound_ctrl_tlast  ( o_outbound_ctrl_tlast  )
    , .outbound_ctrl_tvalid ( o_outbound_ctrl_tvalid )
    , .outbound_ctrl_tready ( i_outbound_ctrl_tready )
    // Mesh AXI4-streams
    // - Inbound
    , .inbound_mesh_tdata   ( i_inbound_mesh_tdata   )
    , .inbound_mesh_tlast   ( i_inbound_mesh_tlast   )
    , .inbound_mesh_tvalid  ( i_inbound_mesh_tvalid  )
    , .inbound_mesh_tready  ( o_inbound_mesh_tready  )
    // - Outbound
    , .outbound_mesh_tdata  ( o_outbound_mesh_tdata  )
    , .outbound_mesh_tlast  ( o_outbound_mesh_tlast  )
    , .outbound_mesh_tvalid ( o_outbound_mesh_tvalid )
    , .outbound_mesh_tready ( i_outbound_mesh_tready )
);

// =============================================================================
// Tracing
// =============================================================================

// Wave tracing
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
