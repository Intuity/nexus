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

`include "nx_common.svh"

// nx_node_distributor
// Routes messages to one of the four output ports
//
module nx_node_distributor
import NXConstants::*;
(
      input  logic                          i_clk
    , input  logic                          i_rst
    // Control signals
    , input  node_id_t                      i_node_id
    , output logic                          o_idle
    // Message to send
    , input  node_message_t                 i_outbound_data
    , input  logic                          i_outbound_valid
    , output logic                          o_outbound_ready
    // Outbound interfaces
    , output logic [3:0][MESSAGE_WIDTH-1:0] o_external_data
    , output logic [3:0]                    o_external_valid
    , input  logic [3:0]                    i_external_ready
    , input  logic [3:0]                    i_external_present
);

direction_t outbound_dir;

// Determine target direction based on several factors:
//  - Target row & column set the initial direction
//  - If a particular direction is absent, routes to the next clockwise stream
//  - Route horizontally (east-west) first, route vertically as a lower priority
//
always_comb begin : comb_outbound_dir
    logic lt_row, gt_row, lt_col, gt_col;
    lt_row = (i_outbound_data.raw.header.target.row    < i_node_id.row   );
    gt_row = (i_outbound_data.raw.header.target.row    > i_node_id.row   );
    lt_col = (i_outbound_data.raw.header.target.column < i_node_id.column);
    gt_col = (i_outbound_data.raw.header.target.column > i_node_id.column);
    casez ({ lt_row, gt_row, lt_col, gt_col, i_external_present })
        // Route horizontally:
        // <R    >R    <C    >C   PRSNT
        { 1'b?, 1'b?, 1'b1, 1'b0, 4'b1??? }: outbound_dir = DIRECTION_WEST;
        { 1'b?, 1'b?, 1'b1, 1'b0, 4'b0??? }: outbound_dir = DIRECTION_NORTH;
        { 1'b?, 1'b?, 1'b0, 1'b1, 4'b??1? }: outbound_dir = DIRECTION_EAST;
        { 1'b?, 1'b?, 1'b0, 1'b1, 4'b??0? }: outbound_dir = DIRECTION_SOUTH;
        // Route vertically:
        // <R    >R    <C    >C   PRSNT
        { 1'b1, 1'b0, 1'b0, 1'b0, 4'b???1 }: outbound_dir = DIRECTION_NORTH;
        { 1'b1, 1'b0, 1'b0, 1'b0, 4'b???0 }: outbound_dir = DIRECTION_EAST;
        { 1'b0, 1'b1, 1'b0, 1'b0, 4'b?1?? }: outbound_dir = DIRECTION_SOUTH;
        { 1'b0, 1'b1, 1'b0, 1'b0, 4'b?0?? }: outbound_dir = DIRECTION_WEST;
        default: outbound_dir = DIRECTION_NORTH;
    endcase
end

nx_stream_distributor #(
      .STREAMS          ( 4                )
) u_distributor (
      .i_clk            ( i_clk            )
    , .i_rst            ( i_rst            )
    // Idle flag
    , .o_idle           ( o_idle           )
    // Inbound message stream
    , .i_inbound_dir    ( outbound_dir     )
    , .i_inbound_data   ( i_outbound_data  )
    , .i_inbound_valid  ( i_outbound_valid )
    , .o_inbound_ready  ( o_outbound_ready )
    // Outbound message streams
    , .o_outbound_data  ( o_external_data  )
    , .o_outbound_valid ( o_external_valid )
    , .i_outbound_ready ( i_external_ready )
);

endmodule : nx_node_distributor
