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

module testbench
import NXConstants::*,
       nx_primitives::ROUND_ROBIN;
(
      input  logic          rst
    // Inbound message streams
    // - North
    , input  node_message_t i_north_data
    , input  logic          i_north_valid
    , output logic          o_north_ready
    // - East
    , input  node_message_t i_east_data
    , input  logic          i_east_valid
    , output logic          o_east_ready
    // - South
    , input  node_message_t i_south_data
    , input  logic          i_south_valid
    , output logic          o_south_ready
    // - West
    , input  node_message_t i_west_data
    , input  logic          i_west_valid
    , output logic          o_west_ready
    // Outbound stream
    , output node_message_t o_outbound_data
    , output logic          o_outbound_valid
    , input  logic          i_outbound_ready
);

// =============================================================================
// Clock Generation
// =============================================================================

reg clk = 1'b0;
always #1 clk <= ~clk;

// =============================================================================
// Shims
// =============================================================================

logic [3:0][MESSAGE_WIDTH-1:0] inbound_data;
logic [3:0]                    inbound_valid, inbound_ready;

assign inbound_data[DIRECTION_NORTH] = i_north_data;
assign inbound_data[DIRECTION_EAST ] = i_east_data;
assign inbound_data[DIRECTION_SOUTH] = i_south_data;
assign inbound_data[DIRECTION_WEST ] = i_west_data;

assign inbound_valid[DIRECTION_NORTH] = i_north_valid;
assign inbound_valid[DIRECTION_EAST ] = i_east_valid;
assign inbound_valid[DIRECTION_SOUTH] = i_south_valid;
assign inbound_valid[DIRECTION_WEST ] = i_west_valid;

assign o_north_ready = inbound_ready[DIRECTION_NORTH];
assign o_east_ready  = inbound_ready[DIRECTION_EAST ];
assign o_south_ready = inbound_ready[DIRECTION_SOUTH];
assign o_west_ready  = inbound_ready[DIRECTION_WEST ];

// =============================================================================
// DUT Instance
// =============================================================================

nx_stream_arbiter #(
      .STREAMS          ( 4                )
    , .SCHEME           ( ROUND_ROBIN      )
) u_dut (
      .i_clk            ( clk              )
    , .i_rst            ( rst              )
    // Inbound message streams
    , .i_inbound_data   ( inbound_data     )
    , .i_inbound_valid  ( inbound_valid    )
    , .o_inbound_ready  ( inbound_ready    )
    // Outbound stream
    , .o_outbound_data  ( o_outbound_data  )
    , .o_outbound_valid ( o_outbound_valid )
    , .i_outbound_ready ( i_outbound_ready )
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
