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
    , parameter MAX_IO         = ((INPUTS > OUTPUTS) ? INPUTS : OUTPUTS)
) (
      input  logic                    rst
    // Node identity
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
    // Inbound message stream
    , input  logic [STREAM_WIDTH-1:0] msg_data_i
    , input  logic [             1:0] msg_dir_i
    , input  logic                    msg_valid_i
    , output logic                    msg_ready_o
    // Outbound bypass message stream
    , output logic [STREAM_WIDTH-1:0] bypass_data_o
    , output logic [             1:0] bypass_dir_o
    , output logic                    bypass_valid_o
    , input  logic                    bypass_ready_i
    // I/O mapping handling
    , output logic [ $clog2(MAX_IO)-1:0] map_io_o
    , output logic                       map_input_o
    , output logic [ ADDR_ROW_WIDTH-1:0] map_remote_row_o
    , output logic [ ADDR_COL_WIDTH-1:0] map_remote_col_o
    , output logic [$clog2(OUTPUTS)-1:0] map_remote_idx_o
    , output logic                       map_slot_o
    , output logic                       map_broadcast_o
    , output logic                       map_seq_o
    , output logic                       map_valid_o
    // Signal state update
    , output logic [ ADDR_ROW_WIDTH-1:0] signal_remote_row_o
    , output logic [ ADDR_COL_WIDTH-1:0] signal_remote_col_o
    , output logic [$clog2(OUTPUTS)-1:0] signal_remote_idx_o
    , output logic                       signal_state_o
    , output logic                       signal_valid_o
    // Instruction load
    , output logic                   instr_core_o
    , output logic [INSTR_WIDTH-1:0] instr_data_o
    , output logic                   instr_valid_o
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
    // Node identity
    , .node_row_i(node_row_i)
    , .node_col_i(node_col_i)
    // Inbound message stream
    , .msg_data_i (msg_data_i )
    , .msg_dir_i  (msg_dir_i  )
    , .msg_valid_i(msg_valid_i)
    , .msg_ready_o(msg_ready_o)
    // Outbound bypass message stream
    , .bypass_data_o (bypass_data_o )
    , .bypass_dir_o  (bypass_dir_o  )
    , .bypass_valid_o(bypass_valid_o)
    , .bypass_ready_i(bypass_ready_i)
    // I/O mapping handling
    , .map_io_o        (map_io_o        )
    , .map_input_o     (map_input_o     )
    , .map_remote_row_o(map_remote_row_o)
    , .map_remote_col_o(map_remote_col_o)
    , .map_remote_idx_o(map_remote_idx_o)
    , .map_slot_o      (map_slot_o      )
    , .map_broadcast_o (map_broadcast_o )
    , .map_seq_o       (map_seq_o       )
    , .map_valid_o     (map_valid_o     )
    // Signal state update
    , .signal_remote_row_o(signal_remote_row_o)
    , .signal_remote_col_o(signal_remote_col_o)
    , .signal_remote_idx_o(signal_remote_idx_o)
    , .signal_state_o     (signal_state_o     )
    , .signal_valid_o     (signal_valid_o     )
    // Instruction load
    , .instr_core_o (instr_core_o )
    , .instr_data_o (instr_data_o )
    , .instr_valid_o(instr_valid_o)
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
