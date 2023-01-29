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

module testbench
import NXConstants::*;
(
      input  logic          rst
    // Idle flag
    , output logic          o_idle
    // Inbound message stream
    , input  direction_t    i_inbound_dir
    , input  node_message_t i_inbound_data
    , input  logic          i_inbound_valid
    , output logic          o_inbound_ready
    // Outbound distributed message streams
    // - North
    , output node_message_t o_north_data
    , output logic          o_north_valid
    , input  logic          i_north_ready
    // - East
    , output node_message_t o_east_data
    , output logic          o_east_valid
    , input  logic          i_east_ready
    // - South
    , output node_message_t o_south_data
    , output logic          o_south_valid
    , input  logic          i_south_ready
    // - West
    , output node_message_t o_west_data
    , output logic          o_west_valid
    , input  logic          i_west_ready
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// Shims
// =============================================================================

logic [3:0][MESSAGE_WIDTH-1:0] outbound_data;
logic [3:0]                    outbound_valid, outbound_ready;

assign o_north_data = outbound_data[DIRECTION_NORTH];
assign o_east_data  = outbound_data[DIRECTION_EAST ];
assign o_south_data = outbound_data[DIRECTION_SOUTH];
assign o_west_data  = outbound_data[DIRECTION_WEST ];

assign o_north_valid = outbound_valid[DIRECTION_NORTH];
assign o_east_valid  = outbound_valid[DIRECTION_EAST ];
assign o_south_valid = outbound_valid[DIRECTION_SOUTH];
assign o_west_valid  = outbound_valid[DIRECTION_WEST ];

assign outbound_ready[DIRECTION_NORTH] = i_north_ready;
assign outbound_ready[DIRECTION_EAST ] = i_east_ready;
assign outbound_ready[DIRECTION_SOUTH] = i_south_ready;
assign outbound_ready[DIRECTION_WEST ] = i_west_ready;

// =============================================================================
// DUT Instance
// =============================================================================

nx_stream_distributor #(
      .STREAMS          ( 4               )
) u_dut (
      .i_clk            ( clk             )
    , .i_rst            ( rst             )
    // Idle flag
    , .o_idle           ( o_idle          )
    // Inbound message stream
    , .i_inbound_dir    ( i_inbound_dir   )
    , .i_inbound_data   ( i_inbound_data  )
    , .i_inbound_valid  ( i_inbound_valid )
    , .o_inbound_ready  ( o_inbound_ready )
    // Outbound message streams
    , .o_outbound_data  ( outbound_data   )
    , .o_outbound_valid ( outbound_valid  )
    , .i_outbound_ready ( outbound_ready  )
);

// =============================================================================
// Tracing
// =============================================================================

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
