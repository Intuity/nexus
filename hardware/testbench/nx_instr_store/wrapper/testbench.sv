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
      parameter INSTR_WIDTH =  15
    , parameter MAX_INSTRS  = 512
) (
      input  logic rst
    // Instruction load interface
    , input  logic                   store_core_i
    , input  logic [INSTR_WIDTH-1:0] store_data_i
    , input  logic                   store_valid_i
    // Populated instruction counters
    , output logic [$clog2(MAX_INSTRS)-1:0] core_0_populated_o
    , output logic [$clog2(MAX_INSTRS)-1:0] core_1_populated_o
    // Instruction fetch interfaces
    // - Core 0
    , input  logic [$clog2(MAX_INSTRS)-1:0] core_0_addr_i
    , input  logic                          core_0_rd_i
    , output logic [       INSTR_WIDTH-1:0] core_0_data_o
    , output logic                          core_0_stall_o
    // - Core 1
    , input  logic [$clog2(MAX_INSTRS)-1:0] core_1_addr_i
    , input  logic                          core_1_rd_i
    , output logic [       INSTR_WIDTH-1:0] core_1_data_o
    , output logic                          core_1_stall_o
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_instr_store #(
      .INSTR_WIDTH(INSTR_WIDTH)
    , .MAX_INSTRS (MAX_INSTRS )
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Instruction load interface
    , .store_core_i (store_core_i )
    , .store_data_i (store_data_i )
    , .store_valid_i(store_valid_i)
    // Populated instruction counters
    , .core_0_populated_o(core_0_populated_o)
    , .core_1_populated_o(core_1_populated_o)
    // Instruction fetch interfaces
    // - Core 0
    , .core_0_addr_i (core_0_addr_i )
    , .core_0_rd_i   (core_0_rd_i   )
    , .core_0_data_o (core_0_data_o )
    , .core_0_stall_o(core_0_stall_o)
    // - Core 1
    , .core_1_addr_i (core_1_addr_i )
    , .core_1_rd_i   (core_1_rd_i   )
    , .core_1_data_o (core_1_data_o )
    , .core_1_stall_o(core_1_stall_o)
);

`ifdef sim_icarus
initial begin : i_vcd
    string f_name;
    $timeformat(-9, 2, " ns", 20);
    if ($value$plusargs("VCD_FILE=%s", f_name)) begin
        $display("%0t: Capturing VCD file %s", $time, f_name);
        $dumpfile(f_name);
        $dumpvars(0, testbench);
    end else begin
        $display("%0t: No VCD filename provided - disabling VCD capture", $time);
    end
end
`endif // sim_icarus

endmodule : testbench
