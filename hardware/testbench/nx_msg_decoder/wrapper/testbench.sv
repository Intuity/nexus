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
      parameter STREAM_WIDTH   = 32
    , parameter ADDR_ROW_WIDTH =  4
    , parameter ADDR_COL_WIDTH =  4
    , parameter COMMAND_WIDTH  =  2
    , parameter INSTR_WIDTH    = 15
    , parameter INPUTS         =  8
    , parameter OUTPUTS        =  8
) (
      input  logic                    rst
    // Node identity
    , output logic                      idle_o
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
    // Inbound message stream
    , input  nx_message_t   msg_data_i
    , input  nx_direction_t msg_dir_i
    , input  logic          msg_valid_i
    , output logic          msg_ready_o
    // I/O mapping handling
    , output logic [$clog2(OUTPUTS)-1:0] map_idx_o     // Output to configure
    , output logic [ ADDR_ROW_WIDTH-1:0] map_tgt_row_o // Target node's row
    , output logic [ ADDR_COL_WIDTH-1:0] map_tgt_col_o // Target node's column
    , output logic [ $clog2(INPUTS)-1:0] map_tgt_idx_o // Target node's I/O index
    , output logic                       map_tgt_seq_o // Target node's input is sequential
    , output logic                       map_valid_o   // Mapping is valid
    // Signal state update
    , output logic [$clog2(INPUTS)-1:0] signal_index_o  // Input index
    , output logic                      signal_is_seq_o // Input is sequential
    , output logic                      signal_state_o  // Signal state
    , output logic                      signal_valid_o  // Update is valid
    // Instruction load
    , output logic [INSTR_WIDTH-1:0] instr_data_o  // Instruction data
    , output logic                   instr_valid_o // Instruction valid
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_msg_decoder #(
      .STREAM_WIDTH  (STREAM_WIDTH  )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
    , .INSTR_WIDTH   (INSTR_WIDTH   )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
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
