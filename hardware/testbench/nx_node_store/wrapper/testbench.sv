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
      parameter INSTR_WIDTH =  15 // Width of each instruction
    , parameter MAX_INSTRS  = 512 // Maximum number of instructions per core
    , parameter CTRL_WIDTH  =  12 // Width of each control entry
    , parameter MAX_CTRL    = 512 // Maximum number of control entries
) (
      input  logic rst
    // Populated instruction counter
    , output logic [$clog2(MAX_INSTRS)-1:0] instr_count_o
    // Instruction load interface
    , input  logic [INSTR_WIDTH-1:0] store_data_i
    , input  logic                   store_valid_i
    // Instruction fetch interfaces
    , input  logic [$clog2(MAX_INSTRS)-1:0] fetch_addr_i
    , input  logic                          fetch_rd_i
    , output logic [       INSTR_WIDTH-1:0] fetch_data_o
    , output logic                          fetch_stall_o
    // Control block interface
    , input  logic [$clog2(MAX_CTRL)-1:0] ctrl_addr_i
    , input  logic [      CTRL_WIDTH-1:0] ctrl_wr_data_i
    , input  logic                        ctrl_wr_en_i
    , input  logic                        ctrl_rd_en_i
    , output logic [      CTRL_WIDTH-1:0] ctrl_rd_data_o
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_node_store #(
      .INSTR_WIDTH(INSTR_WIDTH)
    , .MAX_INSTRS (MAX_INSTRS )
    , .CTRL_WIDTH (CTRL_WIDTH )
    , .MAX_CTRL   (MAX_CTRL   )
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Populated instruction counter
    , .instr_count_o(instr_count_o)
    // Instruction load interface
    , .store_data_i (store_data_i )
    , .store_valid_i(store_valid_i)
    // Instruction fetch interfaces
    , .fetch_addr_i (fetch_addr_i )
    , .fetch_rd_i   (fetch_rd_i   )
    , .fetch_data_o (fetch_data_o )
    , .fetch_stall_o(fetch_stall_o)
    // Control block interface
    , .ctrl_addr_i   (ctrl_addr_i   )
    , .ctrl_wr_data_i(ctrl_wr_data_i)
    , .ctrl_wr_en_i  (ctrl_wr_en_i  )
    , .ctrl_rd_en_i  (ctrl_rd_en_i  )
    , .ctrl_rd_data_o(ctrl_rd_data_o)
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
