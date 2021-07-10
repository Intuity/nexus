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
      parameter AXI4_DATA_WIDTH =                  64
    , parameter AXI4_STRB_WIDTH = AXI4_DATA_WIDTH / 8
    , parameter AXI4_ID_WIDTH   =                   1
) (
      input  wire rst
    // Inbound AXI4-stream
    , input  wire [AXI4_DATA_WIDTH-1:0] inbound_tdata_i
    , input  wire [AXI4_STRB_WIDTH-1:0] inbound_tkeep_i
    , input  wire [AXI4_STRB_WIDTH-1:0] inbound_tstrb_i
    , input  wire [  AXI4_ID_WIDTH-1:0] inbound_tid_i
    , input  wire                       inbound_tlast_i
    , input  wire                       inbound_tvalid_i
    , output wire                       inbound_tready_o
    // Outbound AXI4-stream
    , output wire [AXI4_DATA_WIDTH-1:0] outbound_tdata_o
    , output wire [AXI4_STRB_WIDTH-1:0] outbound_tkeep_o
    , output wire [AXI4_STRB_WIDTH-1:0] outbound_tstrb_o
    , output wire [  AXI4_ID_WIDTH-1:0] outbound_tid_o
    , output wire                       outbound_tlast_o
    , output wire                       outbound_tvalid_o
    , input  wire                       outbound_tready_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_artix_200t #(
      .AXI4_DATA_WIDTH(AXI4_DATA_WIDTH)
    , .AXI4_STRB_WIDTH(AXI4_STRB_WIDTH)
    , .AXI4_ID_WIDTH  (AXI4_ID_WIDTH  )
) dut (
      .clk_i ( clk)
    , .rstn_i(~rst)
    // Inbound AXI4-stream
    , .inbound_tdata_i (inbound_tdata_i )
    , .inbound_tkeep_i (inbound_tkeep_i )
    , .inbound_tstrb_i (inbound_tstrb_i )
    , .inbound_tid_i   (inbound_tid_i   )
    , .inbound_tlast_i (inbound_tlast_i )
    , .inbound_tvalid_i(inbound_tvalid_i)
    , .inbound_tready_o(inbound_tready_o)
    // Outbound AXI4-stream
    , .outbound_tdata_o (outbound_tdata_o )
    , .outbound_tkeep_o (outbound_tkeep_o )
    , .outbound_tstrb_o (outbound_tstrb_o )
    , .outbound_tid_o   (outbound_tid_o   )
    , .outbound_tlast_o (outbound_tlast_o )
    , .outbound_tvalid_o(outbound_tvalid_o)
    , .outbound_tready_i(outbound_tready_i)
);

// Wave tracing
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
