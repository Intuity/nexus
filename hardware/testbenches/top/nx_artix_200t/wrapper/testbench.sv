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
    // Inbound AXI4-stream
    , input  wire [AXI4_DATA_WIDTH-1:0] i_inbound_tdata
    , input  wire                       i_inbound_tlast
    , input  wire                       i_inbound_tvalid
    , output wire                       o_inbound_tready
    // Outbound AXI4-stream
    , output wire [AXI4_DATA_WIDTH-1:0] o_outbound_tdata
    , output wire                       o_outbound_tlast
    , output wire                       o_outbound_tvalid
    , input  wire                       i_outbound_tready
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
      .AXI4_DATA_WIDTH ( AXI4_DATA_WIDTH   )
    , .ROWS            ( ROWS              )
    , .COLUMNS         ( COLUMNS           )
) u_dut (
      .clk             (  clk              )
    , .rstn            ( ~rst              )
    // Status
    , .status_active   ( o_status_active   )
    , .status_idle     ( o_status_idle     )
    , .status_trigger  ( o_status_trigger  )
    // Inbound AXI4-stream
    , .inbound_tdata   ( i_inbound_tdata   )
    , .inbound_tlast   ( i_inbound_tlast   )
    , .inbound_tvalid  ( i_inbound_tvalid  )
    , .inbound_tready  ( o_inbound_tready  )
    // Outbound AXI4-stream
    , .outbound_tdata  ( o_outbound_tdata  )
    , .outbound_tlast  ( o_outbound_tlast  )
    , .outbound_tvalid ( o_outbound_tvalid )
    , .outbound_tready ( i_outbound_tready )
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
