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
    parameter AXI4_DATA_WIDTH = 128
) (
      input  wire rst
    // Status
    , output wire status_active
    , output wire status_idle
    , output wire status_trigger
    // Control AXI4-streams
    // - Inbound
    , input  wire [AXI4_DATA_WIDTH-1:0] inbound_ctrl_tdata_i
    , input  wire                       inbound_ctrl_tlast_i
    , input  wire                       inbound_ctrl_tvalid_i
    , output wire                       inbound_ctrl_tready_o
    // - Outbound
    , output wire [AXI4_DATA_WIDTH-1:0] outbound_ctrl_tdata_o
    , output wire                       outbound_ctrl_tlast_o
    , output wire                       outbound_ctrl_tvalid_o
    , input  wire                       outbound_ctrl_tready_i
    // Mesh AXI4-streams
    // - Inbound
    , input  wire [AXI4_DATA_WIDTH-1:0] inbound_mesh_tdata_i
    , input  wire                       inbound_mesh_tlast_i
    , input  wire                       inbound_mesh_tvalid_i
    , output wire                       inbound_mesh_tready_o
    // - Outbound
    , output wire [AXI4_DATA_WIDTH-1:0] outbound_mesh_tdata_o
    , output wire                       outbound_mesh_tlast_o
    , output wire                       outbound_mesh_tvalid_o
    , input  wire                       outbound_mesh_tready_i
);

reg clk = 1'b0;
always #1 clk <= ~clk;

nx_artix_200t #(
    .AXI4_DATA_WIDTH(AXI4_DATA_WIDTH)
) dut (
      .clk ( clk)
    , .rstn(~rst)
    // Status
    , .status_active (status_active )
    , .status_idle   (status_idle   )
    , .status_trigger(status_trigger)
    // Control AXI4-streams
    // - Inbound
    , .inbound_ctrl_tdata  (inbound_ctrl_tdata_i  )
    , .inbound_ctrl_tlast  (inbound_ctrl_tlast_i  )
    , .inbound_ctrl_tvalid (inbound_ctrl_tvalid_i )
    , .inbound_ctrl_tready (inbound_ctrl_tready_o )
    // - Outbound
    , .outbound_ctrl_tdata (outbound_ctrl_tdata_o )
    , .outbound_ctrl_tlast (outbound_ctrl_tlast_o )
    , .outbound_ctrl_tvalid(outbound_ctrl_tvalid_o)
    , .outbound_ctrl_tready(outbound_ctrl_tready_i)
    // Mesh AXI4-streams
    // - Inbound
    , .inbound_mesh_tdata  (inbound_mesh_tdata_i  )
    , .inbound_mesh_tlast  (inbound_mesh_tlast_i  )
    , .inbound_mesh_tvalid (inbound_mesh_tvalid_i )
    , .inbound_mesh_tready (inbound_mesh_tready_o )
    // - Outbound
    , .outbound_mesh_tdata (outbound_mesh_tdata_o )
    , .outbound_mesh_tlast (outbound_mesh_tlast_o )
    , .outbound_mesh_tvalid(outbound_mesh_tvalid_o)
    , .outbound_mesh_tready(outbound_mesh_tready_i)
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
