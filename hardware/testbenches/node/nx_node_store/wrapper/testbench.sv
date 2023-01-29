// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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
      parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic                  rst
    // Write port
    , input  logic [RAM_ADDR_W-1:0] i_ld_addr
    , input  logic [RAM_DATA_W-1:0] i_ld_wr_data
    , input  logic                  i_ld_wr_en
    // Read ports
    // - A
    , input  logic [RAM_ADDR_W-1:0] i_a_addr
    , input  logic                  i_a_rd_en
    , output logic [RAM_DATA_W-1:0] o_a_rd_data
    , output logic                  o_a_stall
    // - B
    , input  logic [RAM_ADDR_W-1:0] i_b_addr
    , input  logic                  i_b_rd_en
    , output logic [RAM_DATA_W-1:0] o_b_rd_data
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// DUT Instance
// =============================================================================

nx_node_store #(
      .RAM_ADDR_W ( RAM_ADDR_W )
    , .RAM_DATA_W ( RAM_DATA_W )
) u_dut (
      .i_clk        ( clk          )
    , .i_rst        ( rst          )
    // Write port
    , .i_wr_addr    ( i_ld_addr    )
    , .i_wr_data    ( i_ld_wr_data )
    , .i_wr_en      ( i_ld_wr_en   )
    // Read ports
    // - A
    , .i_a_rd_addr  ( i_a_addr     )
    , .i_a_rd_en    ( i_a_rd_en    )
    , .o_a_rd_data  ( o_a_rd_data  )
    , .o_a_rd_stall ( o_a_stall    )
    // - B
    , .i_b_rd_addr  ( i_b_addr     )
    , .i_b_rd_en    ( i_b_rd_en    )
    , .o_b_rd_data  ( o_b_rd_data  )
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
