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
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_msg_decoder #(
      .STREAM_WIDTH  (STREAM_WIDTH  )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
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
