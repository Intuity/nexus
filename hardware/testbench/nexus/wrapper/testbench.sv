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

`include "nx_constants.svh"

module testbench #(
      parameter ROWS           =   6
    , parameter COLUMNS        =   6
    , parameter ADDR_ROW_WIDTH =   4
    , parameter ADDR_COL_WIDTH =   4
    , parameter COMMAND_WIDTH  =   2
    , parameter INSTR_WIDTH    =  21
    , parameter INPUTS         =  32
    , parameter OUTPUTS        =  32
    , parameter REGISTERS      =   8
    , parameter MAX_INSTRS     = 512
    , parameter OPCODE_WIDTH   =   3
) (
      input  logic rst
    // Status signals
    , output logic status_active_o
    , output logic status_idle_o
    , output logic status_trigger_o
    // Control message streams
    // - Inbound
    , input  nx_message_t ctrl_ib_data_i
    , input  logic        ctrl_ib_valid_i
    , output logic        ctrl_ib_ready_o
    // - Outbound
    , output nx_message_t ctrl_ob_data_o
    , output logic        ctrl_ob_valid_o
    , input  logic        ctrl_ob_ready_i
    // Mesh message streams
    // - Inbound
    , input  nx_message_t mesh_ib_data_i
    , input  logic        mesh_ib_valid_i
    , output logic        mesh_ib_ready_o
    // - Outbound
    , output nx_message_t mesh_ob_data_o
    , output logic        mesh_ob_valid_o
    , input  logic        mesh_ob_ready_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nexus #(
      .ROWS          (ROWS          )
    , .COLUMNS       (COLUMNS       )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
    , .INSTR_WIDTH   (INSTR_WIDTH   )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
    , .REGISTERS     (REGISTERS     )
    , .MAX_INSTRS    (MAX_INSTRS    )
    , .OPCODE_WIDTH  (OPCODE_WIDTH  )
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    , .*
);

// Debug probing signals
logic [ROWS-1:0][COLUMNS-1:0] debug_valid;
logic [ROWS-1:0][COLUMNS-1:0] debug_ready;

generate
genvar row, col;
for (row = 0; row < ROWS; row = (row + 1)) begin
    for (col = 0; col < COLUMNS; col = (col + 1)) begin
        assign debug_valid[row][col] = dut.mesh.g_rows[row].g_columns[col].node.outbound_dist.dist_valid_i;
        assign debug_ready[row][col] = dut.mesh.g_rows[row].g_columns[col].node.outbound_dist.dist_ready_o;
    end
end
endgenerate

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
