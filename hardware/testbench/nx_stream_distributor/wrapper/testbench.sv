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
      parameter STREAM_WIDTH = 31
    , parameter SKID_BUFFERS = "yes"
) (
      input  logic                    rst
    // Inbound message stream
    , input  logic [STREAM_WIDTH-1:0] dist_data_i
    , input  logic [             1:0] dist_dir_i
    , input  logic                    dist_valid_i
    , output logic                    dist_ready_o
    // Outbound distributed message streams
    // - North
    , output logic [STREAM_WIDTH-1:0] north_data_o
    , output logic                    north_valid_o
    , input  logic                    north_ready_i
    , input  logic                    north_present_i
    // - East
    , output logic [STREAM_WIDTH-1:0] east_data_o
    , output logic                    east_valid_o
    , input  logic                    east_ready_i
    , input  logic                    east_present_i
    // - South
    , output logic [STREAM_WIDTH-1:0] south_data_o
    , output logic                    south_valid_o
    , input  logic                    south_ready_i
    , input  logic                    south_present_i
    // - West
    , output logic [STREAM_WIDTH-1:0] west_data_o
    , output logic                    west_valid_o
    , input  logic                    west_ready_i
    , input  logic                    west_present_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_stream_distributor #(
      .STREAM_WIDTH(STREAM_WIDTH)
    , .SKID_BUFFERS(SKID_BUFFERS)
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Inbound message stream
    , .dist_data_i (dist_data_i )
    , .dist_dir_i  (dist_dir_i  )
    , .dist_valid_i(dist_valid_i)
    , .dist_ready_o(dist_ready_o)
    // Outbound distributed message streams
    // - North
    , .north_data_o   (north_data_o   )
    , .north_valid_o  (north_valid_o  )
    , .north_ready_i  (north_ready_i  )
    , .north_present_i(north_present_i)
    // - East
    , .east_data_o   (east_data_o   )
    , .east_valid_o  (east_valid_o  )
    , .east_ready_i  (east_ready_i  )
    , .east_present_i(east_present_i)
    // - South
    , .south_data_o   (south_data_o   )
    , .south_valid_o  (south_valid_o  )
    , .south_ready_i  (south_ready_i  )
    , .south_present_i(south_present_i)
    // - West
    , .west_data_o   (west_data_o   )
    , .west_valid_o  (west_valid_o  )
    , .west_ready_i  (west_ready_i  )
    , .west_present_i(west_present_i)
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
