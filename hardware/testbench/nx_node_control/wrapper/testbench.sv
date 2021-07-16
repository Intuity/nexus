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
      parameter STREAM_WIDTH    =  32
    , parameter ADDR_ROW_WIDTH  =   4
    , parameter ADDR_COL_WIDTH  =   4
    , parameter COMMAND_WIDTH   =   2
    , parameter INPUTS          =   8
    , parameter OUTPUTS         =   8
    , parameter OP_STORE_LENGTH = 256
    , parameter OP_STORE_WIDTH  = 1 + ADDR_ROW_WIDTH + ADDR_COL_WIDTH + $clog2(INPUTS) + 1
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
    , input  logic [$clog2(OUTPUTS)-1:0] map_idx_i     // Which output to configure
    , input  logic [ ADDR_ROW_WIDTH-1:0] map_tgt_row_i // Target node's row
    , input  logic [ ADDR_COL_WIDTH-1:0] map_tgt_col_i // Target node's column
    , input  logic [ $clog2(INPUTS)-1:0] map_tgt_idx_i // Target node's input index
    , input  logic                       map_tgt_seq_i // Target node's input is sequential
    , input  logic                       map_valid_i   // Mapping is valid
    // Signal state update
    , input  logic [$clog2(OUTPUTS)-1:0] signal_index_i  // Input index
    , input  logic                       signal_is_seq_i // Input is sequential
    , input  logic                       signal_state_i  // Signal state
    , input  logic                       signal_valid_i  // Update is valid
    // Interface to core
    , output logic               core_trigger_o
    , output logic [ INPUTS-1:0] core_inputs_o
    , input  logic [OUTPUTS-1:0] core_outputs_i
    // Interface to memory
    , output logic [$clog2(OP_STORE_LENGTH)-1:0] store_addr_o    // Output store row address
    , output logic [         OP_STORE_WIDTH-1:0] store_wr_data_o // Output store write data
    , output logic                               store_wr_en_o   // Output store write enable
    , output logic                               store_rd_en_o   // Output store read enable
    , input  logic [         OP_STORE_WIDTH-1:0] store_rd_data_i // Output store read data
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_node_control #(
      .STREAM_WIDTH   (STREAM_WIDTH   )
    , .ADDR_ROW_WIDTH (ADDR_ROW_WIDTH )
    , .ADDR_COL_WIDTH (ADDR_COL_WIDTH )
    , .COMMAND_WIDTH  (COMMAND_WIDTH  )
    , .INPUTS         (INPUTS         )
    , .OUTPUTS        (OUTPUTS        )
    , .OP_STORE_LENGTH(OP_STORE_LENGTH)
    , .OP_STORE_WIDTH (OP_STORE_WIDTH )
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Control signals
    , .idle_o    (idle_o    )
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
    , .map_idx_i    (map_idx_i    )
    , .map_tgt_row_i(map_tgt_row_i)
    , .map_tgt_col_i(map_tgt_col_i)
    , .map_tgt_idx_i(map_tgt_idx_i)
    , .map_tgt_seq_i(map_tgt_seq_i)
    , .map_valid_i  (map_valid_i  )
    // Signal state update
    , .signal_index_i (signal_index_i )
    , .signal_is_seq_i(signal_is_seq_i)
    , .signal_state_i (signal_state_i )
    , .signal_valid_i (signal_valid_i )
    // Interface to core
    , .core_trigger_o(core_trigger_o)
    , .core_inputs_o (core_inputs_o )
    , .core_outputs_i(core_outputs_i)
    // Interface to memory
    , .store_addr_o   (store_addr_o   )
    , .store_wr_data_o(store_wr_data_o)
    , .store_wr_en_o  (store_wr_en_o  )
    , .store_rd_en_o  (store_rd_en_o  )
    , .store_rd_data_i(store_rd_data_i)
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
