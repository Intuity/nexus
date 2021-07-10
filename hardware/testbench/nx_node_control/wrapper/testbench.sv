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
    , parameter ADDR_ROW_WIDTH = 4
    , parameter ADDR_COL_WIDTH = 4
    , parameter COMMAND_WIDTH  =  2
    , parameter INPUTS         =  8
    , parameter OUTPUTS        =  8
    , parameter MAX_IO         = ((INPUTS > OUTPUTS) ? INPUTS : OUTPUTS)
) (
      input  logic rst
    // Node identity
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
    // External trigger signal
    , input  logic trigger_i
    // Channel tokens
    , input  logic token_grant_i
    , output logic token_release_o
    // Outbound message stream
    , output logic [STREAM_WIDTH-1:0] msg_data_o
    , output logic [             1:0] msg_dir_o
    , output logic                    msg_valid_o
    , input  logic                    msg_ready_i
    // I/O mapping
    , input  logic [ $clog2(MAX_IO)-1:0] map_io_i
    , input  logic                       map_input_i
    , input  logic [ ADDR_ROW_WIDTH-1:0] map_remote_row_i
    , input  logic [ ADDR_COL_WIDTH-1:0] map_remote_col_i
    , input  logic [$clog2(OUTPUTS)-1:0] map_remote_idx_i
    , input  logic                       map_slot_i
    , input  logic                       map_broadcast_i
    , input  logic                       map_seq_i
    , input  logic                       map_valid_i
    // Signal state update
    , input  logic [ ADDR_ROW_WIDTH-1:0] signal_remote_row_i
    , input  logic [ ADDR_COL_WIDTH-1:0] signal_remote_col_i
    , input  logic [$clog2(OUTPUTS)-1:0] signal_remote_idx_i
    , input  logic                       signal_state_i
    , input  logic                       signal_valid_i
    // Interface to core
    , output logic               core_trigger_o
    , output logic [ INPUTS-1:0] core_inputs_o
    , input  logic [OUTPUTS-1:0] core_outputs_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_node_control #(
      .STREAM_WIDTH  (STREAM_WIDTH  )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
    , .MAX_IO        (MAX_IO        )
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Node identity
    , .node_row_i(node_row_i)
    , .node_col_i(node_col_i)
    // External trigger signal
    , .trigger_i(trigger_i)
    // Channel tokens
    , .token_grant_i  (token_grant_i  )
    , .token_release_o(token_release_o)
    // Outbound message stream
    , .msg_data_o (msg_data_o )
    , .msg_dir_o  (msg_dir_o  )
    , .msg_valid_o(msg_valid_o)
    , .msg_ready_i(msg_ready_i)
    // I/O mapping
    , .map_io_i        (map_io_i        )
    , .map_input_i     (map_input_i     )
    , .map_remote_row_i(map_remote_row_i)
    , .map_remote_col_i(map_remote_col_i)
    , .map_remote_idx_i(map_remote_idx_i)
    , .map_slot_i      (map_slot_i      )
    , .map_broadcast_i (map_broadcast_i )
    , .map_seq_i       (map_seq_i       )
    , .map_valid_i     (map_valid_i     )
    // Signal state update
    , .signal_remote_row_i(signal_remote_row_i)
    , .signal_remote_col_i(signal_remote_col_i)
    , .signal_remote_idx_i(signal_remote_idx_i)
    , .signal_state_i     (signal_state_i     )
    , .signal_valid_i     (signal_valid_i     )
    // Interface to core
    , .core_trigger_o(core_trigger_o)
    , .core_inputs_o (core_inputs_o )
    , .core_outputs_i(core_outputs_i)
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
