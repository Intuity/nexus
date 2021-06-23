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
      parameter ROWS           =   3
    , parameter COLUMNS        =   3
    , parameter STREAM_WIDTH   =  32
    , parameter ADDR_ROW_WIDTH =   4
    , parameter ADDR_COL_WIDTH =   4
    , parameter COMMAND_WIDTH  =   2
    , parameter INSTR_WIDTH    =  15
    , parameter INPUTS         =   8
    , parameter OUTPUTS        =   8
    , parameter REGISTERS      =   8
    , parameter MAX_INSTRS     = 512
    , parameter OPCODE_WIDTH   =   3
    , parameter COUNTER_WIDTH  =  32
) (
      input  logic rst
    // Control signals
    , input  logic                     active_i
    , output logic [COUNTER_WIDTH-1:0] counter_o
    // Inbound stream
    , input  logic [STREAM_WIDTH-1:0] inbound_data_i
    , input  logic                    inbound_valid_i
    , output logic                    inbound_ready_o
    // Outbound stream
    , output logic [STREAM_WIDTH-1:0] outbound_data_o
    , output logic                    outbound_valid_o
    , input  logic                    outbound_ready_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nexus #(
      .ROWS          (ROWS          )
    , .COLUMNS       (COLUMNS       )
    , .STREAM_WIDTH  (STREAM_WIDTH  )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
    , .INSTR_WIDTH   (INSTR_WIDTH   )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
    , .REGISTERS     (REGISTERS     )
    , .MAX_INSTRS    (MAX_INSTRS    )
    , .OPCODE_WIDTH  (OPCODE_WIDTH  )
    , .COUNTER_WIDTH (COUNTER_WIDTH )
) dut (
      .clk_i(clk)
    , .rst_i(rst)
    // Control signals
    , .active_i (active_i )
    , .counter_o(counter_o)
    // Inbound stream
    , .inbound_data_i (inbound_data_i )
    , .inbound_valid_i(inbound_valid_i)
    , .inbound_ready_o(inbound_ready_o)
    // Outbound stream
    , .outbound_data_o (outbound_data_o )
    , .outbound_valid_o(outbound_valid_o)
    , .outbound_ready_i(outbound_ready_i)
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
