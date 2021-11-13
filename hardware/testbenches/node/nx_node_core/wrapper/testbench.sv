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
      parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter REGISTERS  = 16
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic                        rst
    // I/O from simulated logic
    , input  logic [ INPUTS-1:0]          i_inputs
    , output logic [OUTPUTS-1:0]          o_outputs
    // Execution controls
    , input  logic [NODE_PARAM_WIDTH-1:0] i_populated
    , input  logic                        i_trigger
    , output logic                        o_idle
    // Instruction fetch
    , output logic [RAM_ADDR_W-1:0]       o_instr_addr
    , output logic                        o_instr_rd_en
    , input  logic [RAM_DATA_W-1:0]       i_instr_rd_data
    , input  logic                        i_instr_stall
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// DUT Instance
// =============================================================================

nx_node_core #(
      .INPUTS          ( INPUTS          )
    , .OUTPUTS         ( OUTPUTS         )
    , .REGISTERS       ( REGISTERS       )
    , .RAM_ADDR_W      ( RAM_ADDR_W      )
    , .RAM_DATA_W      ( RAM_DATA_W      )
) u_dut (
      .i_clk           ( clk             )
    , .i_rst           ( rst             )
    // I/O from simulated logic
    , .i_inputs        ( i_inputs        )
    , .o_outputs       ( o_outputs       )
    // Execution controls
    , .i_populated     ( i_populated     )
    , .i_trigger       ( i_trigger       )
    , .o_idle          ( o_idle          )
    // Instruction fetch
    , .o_instr_addr    ( o_instr_addr    )
    , .o_instr_rd_en   ( o_instr_rd_en   )
    , .i_instr_rd_data ( i_instr_rd_data )
    , .i_instr_stall   ( i_instr_stall   )
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
