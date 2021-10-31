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
(
      input  logic          rst
    // Inbound message stream
    , input  node_message_t i_inbound_data
    , input  logic          i_inbound_valid
    , output logic          o_inbound_ready
    // Outbound message stream
    , output node_message_t o_outbound_data
    , output logic          o_outbound_valid
    , input  logic          i_outbound_ready
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// DUT Instance
// =============================================================================

nx_stream_skid dut (
      .i_clk            ( clk              )
    , .i_rst            ( rst              )
    // Inbound message stream
    , .i_inbound_data   ( i_inbound_data   )
    , .i_inbound_valid  ( i_inbound_valid  )
    , .o_inbound_ready  ( o_inbound_ready  )
    // Outbound message stream
    , .o_outbound_data  ( o_outbound_data  )
    , .o_outbound_valid ( o_outbound_valid )
    , .i_outbound_ready ( i_outbound_ready )
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
