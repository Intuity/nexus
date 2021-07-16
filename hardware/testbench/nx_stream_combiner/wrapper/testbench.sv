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
    parameter ARB_SCHEME = "round_robin" // round_robin, prefer_a, prefer_b
) (
      input  logic                    rst
    // Inbound message streams
    // - A
    , input  nx_message_t   stream_a_data_i
    , input  nx_direction_t stream_a_dir_i
    , input  logic          stream_a_valid_i
    , output logic          stream_a_ready_o
    // - B
    , input  nx_message_t   stream_b_data_i
    , input  nx_direction_t stream_b_dir_i
    , input  logic          stream_b_valid_i
    , output logic          stream_b_ready_o
    // Outbound arbitrated message stream
    , output nx_message_t   comb_data_o
    , output nx_direction_t comb_dir_o
    , output logic          comb_valid_o
    , input  logic          comb_ready_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_stream_combiner #(
    .ARB_SCHEME  (ARB_SCHEME)
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Inbound message streams
    // - A
    , .stream_a_data_i (stream_a_data_i )
    , .stream_a_dir_i  (stream_a_dir_i  )
    , .stream_a_valid_i(stream_a_valid_i)
    , .stream_a_ready_o(stream_a_ready_o)
    // - B
    , .stream_b_data_i (stream_b_data_i )
    , .stream_b_dir_i  (stream_b_dir_i  )
    , .stream_b_valid_i(stream_b_valid_i)
    , .stream_b_ready_o(stream_b_ready_o)
    // Outbound arbitrated message stream
    , .comb_data_o (comb_data_o )
    , .comb_dir_o  (comb_dir_o  )
    , .comb_valid_o(comb_valid_o)
    , .comb_ready_i(comb_ready_i)
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
