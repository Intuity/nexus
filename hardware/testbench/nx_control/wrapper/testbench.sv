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
      parameter ROWS       = 3
    , parameter COLUMNS    = 3
    , parameter INPUTS     = 8
    , parameter OUTPUTS    = 8
    , parameter REGISTERS  = 8
) (
      input  logic rst
    // Inbound message stream (from host)
    , input  nx_ctrl_req_t inbound_data_i
    , input  logic         inbound_valid_i
    , output logic         inbound_ready_o
    // Outbound message stream (to host)
    , output nx_ctrl_resp_t outbound_data_o
    , output logic          outbound_valid_o
    , input  logic          outbound_ready_i
    // Externally visible status
    , output logic status_active_o  // High when the mesh is active
    , output logic status_idle_o    // High when the mesh goes idle
    , output logic status_trigger_o // Pulses high on every tick every
    // Interface to the mesh
    , input  logic               mesh_idle_i     // High when mesh fully idle
    , output logic               mesh_trigger_o  // Trigger for the next cycle
    , output logic [COLUMNS-1:0] token_grant_o   // Per-column token emit
    , input  logic [COLUMNS-1:0] token_release_i // Per-column token return
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_control #(
      .ROWS     (ROWS     )
    , .COLUMNS  (COLUMNS  )
    , .INPUTS   (INPUTS   )
    , .OUTPUTS  (OUTPUTS  )
    , .REGISTERS(REGISTERS)
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    , .*
);

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
