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
    parameter STREAM_WIDTH = 32
) (
      input  logic                    rst
    // Inbound message streams
    // - North
    , input  logic [STREAM_WIDTH-1:0] north_data_i
    , input  logic                    north_valid_i
    , output logic                    north_ready_o
    // - East
    , input  logic [STREAM_WIDTH-1:0] east_data_i
    , input  logic                    east_valid_i
    , output logic                    east_ready_o
    // - South
    , input  logic [STREAM_WIDTH-1:0] south_data_i
    , input  logic                    south_valid_i
    , output logic                    south_ready_o
    // - West
    , input  logic [STREAM_WIDTH-1:0] west_data_i
    , input  logic                    west_valid_i
    , output logic                    west_ready_o
    // Outbound arbitrated message stream
    , output logic [STREAM_WIDTH-1:0] arb_data_o
    , output logic [             1:0] arb_dir_o
    , output logic                    arb_valid_o
    , input  logic                    arb_ready_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_stream_arbiter #(
    .STREAM_WIDTH(STREAM_WIDTH)
) dut (
      .clk_i(clk)
    , .rst_i(rst)
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
    // Outbound arbitrated message stream
    , .arb_data_o (arb_data_o )
    , .arb_dir_o  (arb_dir_o  )
    , .arb_valid_o(arb_valid_o)
    , .arb_ready_i(arb_ready_i)
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
