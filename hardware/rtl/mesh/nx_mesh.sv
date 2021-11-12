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

// nx_mesh
// Mesh of nodes with any number of rows or columns.
//
module nx_mesh
import NXConstants::*;
#(
      parameter ROWS       = 3
    , parameter COLUMNS    = 3
    , parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter REGISTERS  = 8
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic               i_clk
    , input  logic               i_rst
    // Control signals
    , input  logic [COLUMNS-1:0] i_trigger
    , output logic [COLUMNS-1:0] o_idle
    // Inbound stream
    , input  node_message_t      i_inbound_data
    , input  logic               i_inbound_valid
    , output logic               o_inbound_ready
    // Outbound stream
    , output node_message_t      o_outbound_data
    , output logic               o_outbound_valid
    , input  logic               i_outbound_ready
);

// =============================================================================
// Internal Signals
// =============================================================================

// I/O bundle for every node
logic [COLUMNS-1:0][ROWS-1:0][3:0][MESSAGE_WIDTH-1:0] mesh_ob_data;
logic [COLUMNS-1:0][ROWS-1:0][3:0]                    mesh_ob_valid;
logic [COLUMNS-1:0][ROWS-1:0][3:0]                    mesh_ib_ready;

// Column grouped idle signals
logic [COLUMNS-1:0][ROWS-1:0] node_idle;
`DECLARE_DQ(COLUMNS, column_idle, i_clk, i_rst, 'd0)

// =============================================================================
// Per-Column Idle Signals
// =============================================================================

// AND reduction for idle signals in each column
generate
for (genvar idx = 0; idx < COLUMNS; idx++) begin : gen_column_idles
    assign column_idle[idx] = &node_idle[idx];
end
endgenerate

// Drive output idle
assign o_idle = column_idle_q;

// =============================================================================
// Link Mesh Ingress/Egress
// =============================================================================

// Ingress
assign o_inbound_ready = mesh_ib_ready[0][0][DIRECTION_NORTH];

// Egress
assign o_outbound_data  = mesh_ob_data[0][ROWS-1][DIRECTION_SOUTH];
assign o_outbound_valid = mesh_ob_valid[0][ROWS-1][DIRECTION_SOUTH];

// =============================================================================
// Generate the Mesh
// =============================================================================

generate
for (genvar idx_row = 0; idx_row < ROWS; idx_row++) begin : gen_rows
    for (genvar idx_col = 0; idx_col < COLUMNS; idx_col++) begin : gen_columns

        // Construct ID
        node_id_t node_id;
        assign node_id.row    = idx_row;
        assign node_id.column = idx_col;

        // Build bundles
        logic [3:0][MESSAGE_WIDTH-1:0] node_ib_data;
        logic [3:0]                    node_ib_valid;
        logic [3:0]                    node_ob_ready;
        logic [3:0]                    node_ob_present;

        // For the top row, only first column has northbound connection
        if (idx_row == 0) begin
            assign node_ib_data[DIRECTION_NORTH]    = (idx_col == 0) ? i_inbound_data  : 'd0;
            assign node_ib_valid[DIRECTION_NORTH]   = (idx_col == 0) ? i_inbound_valid : 'd0;
            assign node_ob_ready[DIRECTION_NORTH]   = 'd0;
            assign node_ob_present[DIRECTION_NORTH] = 'd0;

        // All other rows have a northbound connection to neighbour above
        end else begin
            assign node_ib_data[DIRECTION_NORTH]    = mesh_ob_data[idx_col][idx_row-1][DIRECTION_SOUTH];
            assign node_ib_valid[DIRECTION_NORTH]   = mesh_ob_valid[idx_col][idx_row-1][DIRECTION_SOUTH];
            assign node_ob_ready[DIRECTION_NORTH]   = mesh_ib_ready[idx_col][idx_row-1][DIRECTION_SOUTH];
            assign node_ob_present[DIRECTION_NORTH] = 'd1;

        end

        // For the bottom row, only first column has southbound connection
        if (idx_row == (ROWS - 1)) begin
            assign node_ib_data[DIRECTION_SOUTH]    = 'd0;
            assign node_ib_valid[DIRECTION_SOUTH]   = 'd0;
            assign node_ob_ready[DIRECTION_SOUTH]   = (idx_col == 0) ? i_outbound_ready : 'd0;
            assign node_ob_present[DIRECTION_SOUTH] = (idx_col == 0);

        // All other rows have a southbound connection to the neighbour below
        end else begin
            assign node_ib_data[DIRECTION_SOUTH]    = mesh_ob_data[idx_col][idx_row+1][DIRECTION_NORTH];
            assign node_ib_valid[DIRECTION_SOUTH]   = mesh_ob_valid[idx_col][idx_row+1][DIRECTION_NORTH];
            assign node_ob_ready[DIRECTION_SOUTH]   = mesh_ib_ready[idx_col][idx_row+1][DIRECTION_NORTH];
            assign node_ob_present[DIRECTION_SOUTH] = 'd1;

        end

        // All columns except the last have an eastbound connection
        assign node_ib_data[DIRECTION_EAST]    = (idx_col != (COLUMNS - 1)) ? mesh_ob_data[idx_col+1][idx_row][DIRECTION_WEST]  : 'd0;
        assign node_ib_valid[DIRECTION_EAST]   = (idx_col != (COLUMNS - 1)) ? mesh_ob_valid[idx_col+1][idx_row][DIRECTION_WEST] : 'd0;
        assign node_ob_ready[DIRECTION_EAST]   = (idx_col != (COLUMNS - 1)) ? mesh_ib_ready[idx_col+1][idx_row][DIRECTION_WEST] : 'd0;
        assign node_ob_present[DIRECTION_EAST] = (idx_col != (COLUMNS - 1));

        // All columns except the first have an westbound connection
        assign node_ib_data[DIRECTION_WEST]    = (idx_col != 0) ? mesh_ob_data[idx_col-1][idx_row][DIRECTION_EAST]  : 'd0;
        assign node_ib_valid[DIRECTION_WEST]   = (idx_col != 0) ? mesh_ob_valid[idx_col-1][idx_row][DIRECTION_EAST] : 'd0;
        assign node_ob_ready[DIRECTION_WEST]   = (idx_col != 0) ? mesh_ib_ready[idx_col-1][idx_row][DIRECTION_EAST] : 'd0;
        assign node_ob_present[DIRECTION_WEST] = (idx_col != 0);

        // Node instance
        nx_node #(
              .INPUTS             ( INPUTS                          )
            , .OUTPUTS            ( OUTPUTS                         )
            , .REGISTERS          ( REGISTERS                       )
            , .RAM_ADDR_W         ( RAM_ADDR_W                      )
            , .RAM_DATA_W         ( RAM_DATA_W                      )
        ) u_node (
              .i_clk              ( i_clk                           )
            , .i_rst              ( i_rst                           )
            // Control signals
            , .i_node_id          ( node_id                         )
            , .i_trigger          ( i_trigger[idx_col]              )
            , .o_idle             ( node_idle[idx_col][idx_row]     )
            // Inbound interfaces
            , .i_inbound_data     ( node_ib_data                    )
            , .i_inbound_valid    ( node_ib_valid                   )
            , .o_inbound_ready    ( mesh_ib_ready[idx_col][idx_row] )
            // Outbound interfaces
            , .o_outbound_data    ( mesh_ob_data[idx_col][idx_row]  )
            , .o_outbound_valid   ( mesh_ob_valid[idx_col][idx_row] )
            , .i_outbound_ready   ( node_ob_ready                   )
            , .i_outbound_present ( node_ob_present                 )
        );

    end
end
endgenerate

endmodule : nx_mesh
