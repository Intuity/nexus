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
      parameter ROWS       = 3
    , parameter COLUMNS    = 3
    , parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter REGISTERS  = 16
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic              rst
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
    , output logic              o_ctrl_out_valid
    , input  logic              i_ctrl_out_ready
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// DUT Instance
// =============================================================================

nexus #(
      .ROWS             ( ROWS             )
    , .COLUMNS          ( COLUMNS          )
    , .INPUTS           ( INPUTS           )
    , .OUTPUTS          ( OUTPUTS          )
    , .REGISTERS        ( REGISTERS        )
    , .RAM_ADDR_W       ( RAM_ADDR_W       )
    , .RAM_DATA_W       ( RAM_DATA_W       )
) u_dut (
      .i_clk            ( clk              )
    , .i_rst            ( rst              )
    // Status signals
    , .o_status_active  ( o_status_active  )
    , .o_status_idle    ( o_status_idle    )
    , .o_status_trigger ( o_status_trigger )
    // Inbound control stream
    , .i_ctrl_in_data   ( i_ctrl_in_data   )
    , .i_ctrl_in_valid  ( i_ctrl_in_valid  )
    , .o_ctrl_in_ready  ( o_ctrl_in_ready  )
    // Outbound control stream
    , .o_ctrl_out_data  ( o_ctrl_out_data  )
    , .o_ctrl_out_valid ( o_ctrl_out_valid )
    , .i_ctrl_out_ready ( i_ctrl_out_ready )
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
