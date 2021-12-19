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
    parameter OUTPUTS    = 32
) (
      input  logic               rst
    // Control signals
    , input  node_id_t           i_node_id
    , output logic               o_idle
    // Output signals
    , output logic [OUTPUTS-1:0] o_outputs
    // Inbound interface from mesh
    , input  node_message_t      i_inbound_data
    , input  logic               i_inbound_valid
    , output logic               o_inbound_ready
    // Passthrough interface from neighbouring aggregator
    , input  node_message_t      i_passthrough_data
    , input  logic               i_passthrough_valid
    , output logic               o_passthrough_ready
    // Outbound interfaces
    , output node_message_t      o_outbound_data
    , output logic               o_outbound_valid
    , input  logic               i_outbound_ready
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// DUT Instance
// =============================================================================

nx_aggregator #(
      .OUTPUTS ( OUTPUTS )
) u_dut (
      .i_clk               ( clk                 )
    , .i_rst               ( rst                 )
    // Control signals
    , .i_node_id           ( i_node_id           )
    , .o_idle              ( o_idle              )
    // Output signals
    , .o_outputs           ( o_outputs           )
    // Inbound interface from mesh
    , .i_inbound_data      ( i_inbound_data      )
    , .i_inbound_valid     ( i_inbound_valid     )
    , .o_inbound_ready     ( o_inbound_ready     )
    // Passthrough interface from neighbouring aggregator
    , .i_passthrough_data  ( i_passthrough_data  )
    , .i_passthrough_valid ( i_passthrough_valid )
    , .o_passthrough_ready ( o_passthrough_ready )
    // Outbound interfaces
    , .o_outbound_data     ( o_outbound_data     )
    , .o_outbound_valid    ( o_outbound_valid    )
    , .i_outbound_ready    ( i_outbound_ready    )
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
