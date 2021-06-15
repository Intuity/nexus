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
module nx_mesh #(
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
) (
      input  wire clk_i
    , input  wire rst_i
    // Control signals
    , input  wire trigger_i
    // Inbound stream
    , input  wire [STREAM_WIDTH-1:0] inbound_data_i
    , input  wire                    inbound_valid_i
    , output wire                    inbound_ready_o
    // Outbound stream
    , output wire [STREAM_WIDTH-1:0] outbound_data_o
    , output wire                    outbound_valid_o
    , input  wire                    outbound_ready_i
);

localparam NODES = ROWS * COLUMNS;

wire [STREAM_WIDTH-1:0] north_data [NODES-1:0], east_data [NODES-1:0],
                        south_data [NODES-1:0], west_data [NODES-1:0];
wire                    north_valid [NODES-1:0], east_valid [NODES-1:0],
                        south_valid [NODES-1:0], west_valid [NODES-1:0];
wire                    north_ready [NODES-1:0], east_ready [NODES-1:0],
                        south_ready [NODES-1:0], west_ready [NODES-1:0];

generate
genvar i_row, i_col;
for (i_row = 0; i_row < ROWS; i_row = (i_row + 1)) begin
    for (i_col = 0; i_col < COLUMNS; i_col = (i_col + 1)) begin
        wire [STREAM_WIDTH-1:0] ib_north_data, ib_east_data, ib_south_data,
                                ib_west_data;
        wire                    ib_north_valid, ib_east_valid, ib_south_valid,
                                ib_west_valid;
        wire                    ib_north_ready, ib_east_ready, ib_south_ready,
                                ib_west_ready;

        wire [STREAM_WIDTH-1:0] ob_north_data, ob_east_data, ob_south_data,
                                ob_west_data;
        wire                    ob_north_valid, ob_east_valid, ob_south_valid,
                                ob_west_valid;
        wire                    ob_north_ready, ob_east_ready, ob_south_ready,
                                ob_west_ready;

        if (i_row == 0) begin
            if (i_col == 0) begin
                assign ib_north_data   = inbound_data_i;
                assign ib_north_valid  = inbound_valid_i;
                assign inbound_ready_o = ib_north_ready;

                assign outbound_data_o  = ob_north_data;
                assign outbound_valid_o = ob_north_valid;
                assign ob_north_ready   = outbound_ready_i;
            end else begin
                assign ib_north_data  = {STREAM_WIDTH{1'b0}};
                assign ib_north_valid = 1'b0;
                assign ob_north_ready = 1'b0;
            end
        end else begin
            assign ib_north_data  = south_data [(i_row - 1) * COLUMNS + i_col];
            assign ib_north_valid = south_valid[(i_row - 1) * COLUMNS + i_col];
            assign south_ready[(i_row - 1) * COLUMNS + i_col] = ib_north_ready;

            assign north_data [i_rows * COLUMNS + i_col] = ob_north_data;
            assign north_valid[i_rows * COLUMNS + i_col] = ob_north_valid;
            assign ob_north_ready                        = north_ready;
        end

        if (i_col == (COLUMNS - 1)) begin
            assign ib_east_data  = {STREAM_WIDTH{1'b0}};
            assign ib_east_valid = 1'b0;
            assign ob_east_ready = 1'b0;
        end else begin
            assign ib_east_data  = west_data [i_row * COLUMNS + i_col + 1];
            assign ib_east_valid = west_valid[i_row * COLUMNS + i_col + 1];
            assign west_ready[i_row * COLUMNS + i_col + 1] = ib_east_ready;

            assign east_data [i_rows * COLUMNS + i_col] = ob_east_data;
            assign east_valid[i_rows * COLUMNS + i_col] = ob_east_valid;
            assign ob_east_ready                        = east_ready;
        end

        if (i_row == (ROWS - 1)) begin
            assign ib_south_data  = {STREAM_WIDTH{1'b0}};
            assign ib_south_valid = 1'b0;
            assign ob_south_ready = 1'b0;
        end else begin
            assign ib_south_data  = north_data [(i_row + 1) * COLUMNS + i_col];
            assign ib_south_valid = north_valid[(i_row + 1) * COLUMNS + i_col];
            assign north_ready[(i_row + 1) * COLUMNS + i_col] = ib_south_ready;

            assign south_data [i_rows * COLUMNS + i_col] = ob_south_data;
            assign south_valid[i_rows * COLUMNS + i_col] = ob_south_valid;
            assign ob_south_ready                        = south_ready;
        end

        if (i_col == 0) begin
            assign ib_west_data  = {STREAM_WIDTH{1'b0}};
            assign ib_west_valid = 1'b0;
            assign ob_west_ready = 1'b0;
        end else begin
            assign ib_west_data  = east_data [i_row * COLUMNS + i_col - 1];
            assign ib_west_valid = east_valid[i_row * COLUMNS + i_col - 1];
            assign east_ready[i_row * COLUMNS + i_col - 1] = ib_west_ready;

            assign west_data [i_rows * COLUMNS + i_col] = ob_west_data;
            assign west_valid[i_rows * COLUMNS + i_col] = ob_west_valid;
            assign ob_west_ready                        = west_ready;
        end

        nx_node #(
              .STREAM_WIDTH  (STREAM_WIDTH  )
            , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
            , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
            , .COMMAND_WIDTH (COMMAND_WIDTH )
            , .INSTR_WIDTH   (INSTR_WIDTH   )
            , .INPUTS        (INPUTS        )
            , .OUTPUTS       (OUTPUTS       )
            , .REGISTERS     (REGISTERS     )
            , .MAX_INSTRS    (MAX_INSTRS    )
            , .OPCODE_WIDTH  (OPCODE_WIDTH  )
        ) node (
              .clk_i(clk_i)
            , .rst_i(rst_i)
            // Control signals
            , .trigger_i (trigger_i                )
            , .node_row_i(i_row[ADDR_ROW_WIDTH-1:0])
            , .node_col_i(i_col[ADDR_COL_WIDTH-1:0])
            // Inbound interfaces
            // - North
            , .ib_north_data_i (ib_north_data )
            , .ib_north_valid_i(ib_north_valid)
            , .ib_north_ready_o(ib_north_ready)
            // - East
            , .ib_east_data_i (ib_east_data_i )
            , .ib_east_valid_i(ib_east_valid_i)
            , .ib_east_ready_o(ib_east_ready_o)
            // - South
            , .ib_south_data_i (ib_south_data_i )
            , .ib_south_valid_i(ib_south_valid_i)
            , .ib_south_ready_o(ib_south_ready_o)
            // - West
            , .ib_west_data_i (ib_west_data_i )
            , .ib_west_valid_i(ib_west_valid_i)
            , .ib_west_ready_o(ib_west_ready_o)
            // Outbound interfaces
            // - North
            , .ob_north_data_o (ob_north_data_o )
            , .ob_north_valid_o(ob_north_valid_o)
            , .ob_north_ready_i(ob_north_ready_i)
            // - East
            , .ob_east_data_o (ob_east_data_o )
            , .ob_east_valid_o(ob_east_valid_o)
            , .ob_east_ready_i(ob_east_ready_i)
            // - South
            , .ob_south_data_o (ob_south_data_o )
            , .ob_south_valid_o(ob_south_valid_o)
            , .ob_south_ready_i(ob_south_ready_i)
            // - West
            , .ob_west_data_o (ob_west_data_o )
            , .ob_west_valid_o(ob_west_valid_o)
            , .ob_west_ready_i(ob_west_ready_i)
        );
    end
end
endgenerate

endmodule : nx_mesh
