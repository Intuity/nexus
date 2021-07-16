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
      parameter ADDR_ROW_WIDTH = 4
    , parameter ADDR_COL_WIDTH = 4
) (
      input  logic rst
    // Control signals
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
    // Inbound message streams
    // - North
    , input  nx_message_t north_data_i
    , input  logic        north_valid_i
    , output logic        north_ready_o
    // - East
    , input  nx_message_t east_data_i
    , input  logic        east_valid_i
    , output logic        east_ready_o
    // - South
    , input  nx_message_t south_data_i
    , input  logic        south_valid_i
    , output logic        south_ready_o
    // - West
    , input  nx_message_t west_data_i
    , input  logic        west_valid_i
    , output logic        west_ready_o
    // Outbound stream for this node
    , output nx_message_t internal_data_o
    , output logic        internal_valid_o
    , input  logic        internal_ready_i
    // Outbound stream for bypass
    , output nx_message_t   bypass_data_o
    , output nx_direction_t bypass_dir_o
    , output logic          bypass_valid_o
    , input  logic          bypass_ready_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_stream_arbiter #(
      .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Control signals
    , .node_row_i(node_row_i)
    , .node_col_i(node_col_i)
    // Inbound message streams
    // - North
    , .north_data_i (north_data_i )
    , .north_valid_i(north_valid_i)
    , .north_ready_o(north_ready_o)
    // - East
    , .east_data_i (east_data_i )
    , .east_valid_i(east_valid_i)
    , .east_ready_o(east_ready_o)
    // - South
    , .south_data_i (south_data_i )
    , .south_valid_i(south_valid_i)
    , .south_ready_o(south_ready_o)
    // - West
    , .west_data_i (west_data_i )
    , .west_valid_i(west_valid_i)
    , .west_ready_o(west_ready_o)
    // Outbound stream for this node
    , .internal_data_o (internal_data_o )
    , .internal_valid_o(internal_valid_o)
    , .internal_ready_i(internal_ready_i)
    // Outbound stream for bypass
    , .bypass_data_o (bypass_data_o )
    , .bypass_dir_o  (bypass_dir_o  )
    , .bypass_valid_o(bypass_valid_o)
    , .bypass_ready_i(bypass_ready_i)
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
