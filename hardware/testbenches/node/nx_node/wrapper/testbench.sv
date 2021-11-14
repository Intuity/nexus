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
import NXConstants::*;
#(
      parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter REGISTERS  = 16
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic          rst
    // Control signals
    , input  node_id_t      i_node_id
    , input  logic          i_idle
    , output logic          o_idle
    , input  logic          i_trigger
    , output logic          o_trigger
    // Inbound interfaces
    // - North
    , input  node_message_t i_ib_north_data
    , input  logic          i_ib_north_valid
    , output logic          o_ib_north_ready
    // - East
    , input  node_message_t i_ib_east_data
    , input  logic          i_ib_east_valid
    , output logic          o_ib_east_ready
    // - South
    , input  node_message_t i_ib_south_data
    , input  logic          i_ib_south_valid
    , output logic          o_ib_south_ready
    // - West
    , input  node_message_t i_ib_west_data
    , input  logic          i_ib_west_valid
    , output logic          o_ib_west_ready
    // Outbound interfaces
    // - North
    , output node_message_t o_ob_north_data
    , output logic          o_ob_north_valid
    , input  logic          i_ob_north_ready
    , input  logic          i_ob_north_present
    // - East
    , output node_message_t o_ob_east_data
    , output logic          o_ob_east_valid
    , input  logic          i_ob_east_ready
    , input  logic          i_ob_east_present
    // - South
    , output node_message_t o_ob_south_data
    , output logic          o_ob_south_valid
    , input  logic          i_ob_south_ready
    , input  logic          i_ob_south_present
    // - West
    , output node_message_t o_ob_west_data
    , output logic          o_ob_west_valid
    , input  logic          i_ob_west_ready
    , input  logic          i_ob_west_present
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

assign inbound_data[DIRECTION_NORTH]  = i_ib_north_data;
assign inbound_valid[DIRECTION_NORTH] = i_ib_north_valid;
assign o_ib_north_ready               = inbound_ready[DIRECTION_NORTH];

assign inbound_data[DIRECTION_EAST]  = i_ib_east_data;
assign inbound_valid[DIRECTION_EAST] = i_ib_east_valid;
assign o_ib_east_ready                = inbound_ready[DIRECTION_EAST];

assign inbound_data[DIRECTION_SOUTH]  = i_ib_south_data;
assign inbound_valid[DIRECTION_SOUTH] = i_ib_south_valid;
assign o_ib_south_ready               = inbound_ready[DIRECTION_SOUTH];

assign inbound_data[DIRECTION_WEST]  = i_ib_west_data;
assign inbound_valid[DIRECTION_WEST] = i_ib_west_valid;
assign o_ib_west_ready                = inbound_ready[DIRECTION_WEST];

logic [3:0][MESSAGE_WIDTH-1:0] outbound_data;
logic [3:0]                    outbound_valid, outbound_ready, outbound_present;

assign o_ob_north_data                   = outbound_data[DIRECTION_NORTH];
assign o_ob_north_valid                  = outbound_valid[DIRECTION_NORTH];
assign outbound_ready[DIRECTION_NORTH]   = i_ob_north_ready;
assign outbound_present[DIRECTION_NORTH] = i_ob_north_present;

assign o_ob_east_data                   = outbound_data[DIRECTION_EAST];
assign o_ob_east_valid                  = outbound_valid[DIRECTION_EAST];
assign outbound_ready[DIRECTION_EAST]   = i_ob_east_ready;
assign outbound_present[DIRECTION_EAST] = i_ob_east_present;

assign o_ob_south_data                   = outbound_data[DIRECTION_SOUTH];
assign o_ob_south_valid                  = outbound_valid[DIRECTION_SOUTH];
assign outbound_ready[DIRECTION_SOUTH]   = i_ob_south_ready;
assign outbound_present[DIRECTION_SOUTH] = i_ob_south_present;

assign o_ob_west_data                   = outbound_data[DIRECTION_WEST];
assign o_ob_west_valid                  = outbound_valid[DIRECTION_WEST];
assign outbound_ready[DIRECTION_WEST]   = i_ob_west_ready;
assign outbound_present[DIRECTION_WEST] = i_ob_west_present;

// =============================================================================
// DUT Instance
// =============================================================================

nx_node #(
      .INPUTS             ( INPUTS           )
    , .OUTPUTS            ( OUTPUTS          )
    , .REGISTERS          ( REGISTERS        )
    , .RAM_ADDR_W         ( RAM_ADDR_W       )
    , .RAM_DATA_W         ( RAM_DATA_W       )
) u_dut (
      .i_clk              ( clk              )
    , .i_rst              ( rst              )
    // Control signals
    , .i_node_id          ( i_node_id        )
    , .i_idle             ( i_idle           )
    , .o_idle             ( o_idle           )
    , .i_trigger          ( i_trigger        )
    , .o_trigger          ( o_trigger        )
    // Inbound interfaces
    , .i_inbound_data     ( inbound_data     )
    , .i_inbound_valid    ( inbound_valid    )
    , .o_inbound_ready    ( inbound_ready    )
    // Outbound interfaces
    , .o_outbound_data    ( outbound_data    )
    , .o_outbound_valid   ( outbound_valid   )
    , .i_outbound_ready   ( outbound_ready   )
    , .i_outbound_present ( outbound_present )
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
