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

`include "nx_common.svh"

// nx_mesh
// Mesh of nodes with any number of rows or columns.
//
module nx_mesh
import NXConstants::*;
#(
      parameter ROWS    = 3
    , parameter COLUMNS = 3
    , parameter OUTPUTS = 32
) (
      input  logic                         i_clk
    , input  logic                         i_rst
    // Control signals
    , input  logic [COLUMNS-1:0]           i_trigger
    , output logic [COLUMNS-1:0]           o_node_idle
    , output logic                         o_agg_idle
    // Inbound stream
    , input  node_message_t                i_inbound_data
    , input  logic                         i_inbound_valid
    , output logic                         o_inbound_ready
    // Outbound stream
    , output node_message_t                o_outbound_data
    , output logic                         o_outbound_valid
    , input  logic                         i_outbound_ready
    // Aggregated outputs
    , output logic [(COLUMNS*OUTPUTS)-1:0] o_outputs
    // Memory inputs
    , input  logic [TOP_MEM_COUNT-1:0]     i_mem_enable
    , input  logic [TOP_MEM_COUNT-1:0][TOP_MEM_DATA_WIDTH-1:0] i_mem_rd_data
);

logic _unused;
assign _unused = &{1'b0, i_mem_enable, i_mem_rd_data};

// =============================================================================
// Internal Signals
// =============================================================================

// I/O bundle for every node
logic [COLUMNS-1:0][ROWS-1:0][3:0][MESSAGE_WIDTH-1:0] mesh_ob_data;
logic [COLUMNS-1:0][ROWS-1:0][3:0]                    mesh_ob_valid;
logic [COLUMNS-1:0]                                   mesh_ob_ready;
logic [COLUMNS-1:0][ROWS-1:0][3:0]                    mesh_ib_ready;

// Columnised idle/trigger chaining
logic [COLUMNS-1:0][ROWS-1:0] chain_idle;
logic [COLUMNS-1:0][ROWS-1:0] chain_trigger;

// Register the fully chained and aggregator idle signals
`DECLARE_DQ(COLUMNS, column_idle,  i_clk, i_rst, 'd0)
`DECLARE_DQ(      1, all_agg_idle, i_clk, i_rst, 'd0)

// =============================================================================
// Per-Column Idle Signals
// =============================================================================

// AND reduction for idle signals in each column
generate
for (genvar idx = 0; idx < COLUMNS; idx++) begin : gen_column_idles
    assign column_idle[idx] = chain_idle[idx][0];
end
endgenerate

// Drive idle outputs
assign o_node_idle = column_idle_q;
assign o_agg_idle  = all_agg_idle_q;

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

        // For the bottom row, only outbound connections exist
        if (idx_row == (ROWS - 1)) begin
            assign node_ib_data[DIRECTION_SOUTH]    = 'd0;
            assign node_ib_valid[DIRECTION_SOUTH]   = 'd0;
            assign node_ob_ready[DIRECTION_SOUTH]   = mesh_ob_ready[idx_col];
            assign node_ob_present[DIRECTION_SOUTH] = 'd1;

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

        // Chaining
        logic inbound_idle, inbound_trigger;
        assign inbound_idle = (
            (idx_row == (COLUMNS - 1)) ? 'd1
                                       : chain_idle[idx_col][idx_row+1]
        );
        assign inbound_trigger = (
            (idx_row == 0) ? i_trigger[idx_col]
                           : chain_trigger[idx_col][idx_row-1]
        );

        // Node instance
        nx_node u_node (
              .i_clk              ( i_clk                           )
            , .i_rst              ( i_rst                           )
            // Control signals
            , .i_node_id          ( node_id                         )
            , .i_idle             ( inbound_idle                    )
            , .o_idle             ( chain_idle[idx_col][idx_row]    )
            , .i_trigger          ( inbound_trigger                 )
            , .o_trigger          ( chain_trigger[idx_col][idx_row] )
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

// Mesh ingress ready controlled by node 0, 0
assign o_inbound_ready = mesh_ib_ready[0][0][DIRECTION_NORTH];

// =============================================================================
// Generate the Aggregators
// =============================================================================

logic [COLUMNS-1:0]                    agg_idle;
logic [COLUMNS-1:0][MESSAGE_WIDTH-1:0] agg_data;
logic [COLUMNS-1:0]                    agg_valid, agg_ready;

for (genvar idx_col = 0; idx_col < COLUMNS; idx_col++) begin : gen_aggregators

    // Construct ID
    node_id_t agg_id;
    assign agg_id.row    = ROWS;
    assign agg_id.column = idx_col;

    // Pickup neighbour's passthrough interface
    logic [MESSAGE_WIDTH-1:0] thru_data;
    logic                     thru_valid;
    logic                     thru_ready;

    // - Final column is tied off
    if (idx_col == (COLUMNS - 1)) begin
        logic _unused_col;
        assign thru_data   = 'd0;
        assign thru_valid  = 'd0;
        assign _unused_col = &{ 1'b0, thru_ready };

    // - All other columns are linked to their neighbour
    end else begin
        assign thru_data            = agg_data[idx_col+1];
        assign thru_valid           = agg_valid[idx_col+1];
        assign agg_ready[idx_col+1] = thru_ready;

    end

    // Instance the aggregator
    nx_aggregator #(
          .OUTPUTS             ( OUTPUTS                                         )
    ) u_agg (
          .i_clk               ( i_clk                                           )
        , .i_rst               ( i_rst                                           )
        // Control signals
        , .i_node_id           ( agg_id                                          )
        , .o_idle              ( agg_idle[idx_col]                               )
        // Output signals
        , .o_outputs           ( o_outputs[idx_col*OUTPUTS+:OUTPUTS]             )
        // Inbound interface from mesh
        , .i_inbound_data      ( mesh_ob_data[idx_col][ROWS-1][DIRECTION_SOUTH]  )
        , .i_inbound_valid     ( mesh_ob_valid[idx_col][ROWS-1][DIRECTION_SOUTH] )
        , .o_inbound_ready     ( mesh_ob_ready[idx_col]                          )
        // Passthrough interface from neighbouring aggregator
        , .i_passthrough_data  ( thru_data                                       )
        , .i_passthrough_valid ( thru_valid                                      )
        , .o_passthrough_ready ( thru_ready                                      )
        // Outbound interfaces
        , .o_outbound_data     ( agg_data[idx_col]                               )
        , .o_outbound_valid    ( agg_valid[idx_col]                              )
        , .i_outbound_ready    ( agg_ready[idx_col]                              )
    );

end

// Accumulate aggregator idles
assign all_agg_idle = &agg_idle;

// Link the aggregator in column 0 to the main outbound connection
assign o_outbound_data  = agg_data[0];
assign o_outbound_valid = agg_valid[0];
assign agg_ready[0]     = i_outbound_ready;

endmodule : nx_mesh
