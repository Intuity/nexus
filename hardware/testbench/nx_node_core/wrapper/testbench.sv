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
      parameter INPUTS       =   8
    , parameter OUTPUTS      =   8
    , parameter REGISTERS    =   8
    , parameter MAX_INSTRS   = 512
    , parameter INSTR_WIDTH  =  36
    , parameter OPCODE_WIDTH =   3
) (
      input  logic                          rst
    // I/O from simulated logic
    , input  logic [            INPUTS-1:0] inputs_i
    , output logic [           OUTPUTS-1:0] outputs_o
    // Execution controls
    , input  logic [$clog2(MAX_INSTRS)-1:0] populated_i
    , input  logic                          trigger_i
    , output logic                          idle_o
    // Instruction fetch
    , output logic [$clog2(MAX_INSTRS)-1:0] instr_addr_o
    , output logic                          instr_rd_o
    , input  logic [       INSTR_WIDTH-1:0] instr_data_i
    , input  logic                          instr_stall_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_node_core #(
      .INPUTS      (INPUTS      )
    , .OUTPUTS     (OUTPUTS     )
    , .REGISTERS   (REGISTERS   )
    , .MAX_INSTRS  (MAX_INSTRS  )
    , .INSTR_WIDTH (INSTR_WIDTH )
    , .OPCODE_WIDTH(OPCODE_WIDTH)
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // I/O from simulated logic
    , .inputs_i (inputs_i )
    , .outputs_o(outputs_o)
    // Execution controls
    , .populated_i(populated_i)
    , .trigger_i  (trigger_i  )
    , .idle_o     (idle_o     )
    // Instruction fetch
    , .instr_addr_o (instr_addr_o )
    , .instr_rd_o   (instr_rd_o   )
    , .instr_data_i (instr_data_i )
    , .instr_stall_i(instr_stall_i)
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
