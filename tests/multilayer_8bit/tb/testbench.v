// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

`timescale 1ns/1ps

module testbench();

reg clk, rst;

wire [7:0] sum;
wire overflow;

initial begin
    $display("%0t: Assert reset", $time);
    clk = 1'b0;
    rst = 1'b1;
    repeat (20) @(posedge clk);
    $display("%0t: De-assert reset", $time);
    rst = 1'b0;
    repeat (512) @(posedge clk);
    $display("%0t: End simulation", $time);
    $finish;
end

always #1 clk = ~clk;

Top m_dut(
      .clk(clk)
    , .rst(rst)
    , .sum(sum)
    , .overflow(overflow)
);

// VCD tracing
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

endmodule
