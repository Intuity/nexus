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
    // Inbound message stream
    , input  logic [STREAM_WIDTH-1:0] inbound_data_i
    , input  logic                    inbound_valid_i
    , output logic                    inbound_ready_o
    // Outbound message stream
    , output logic [STREAM_WIDTH-1:0] outbound_data_o
    , output logic                    outbound_valid_o
    , input  logic                    outbound_ready_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_stream_skid #(
    .STREAM_WIDTH(STREAM_WIDTH)
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Inbound message stream
    , .inbound_data_i (inbound_data_i )
    , .inbound_valid_i(inbound_valid_i)
    , .inbound_ready_o(inbound_ready_o)
    // Outbound message stream
    , .outbound_data_o (outbound_data_o )
    , .outbound_valid_o(outbound_valid_o)
    , .outbound_ready_i(outbound_ready_i)
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
