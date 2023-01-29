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

// nx_fifo
// Parameterisable FIFO
//
module nx_fifo #(
      parameter DEPTH    =     2 // How many entries in the FIFO
    , parameter WIDTH    =    32 // The width of each FIFO entry
    , parameter FULL_LVL = DEPTH // The level at which the full flag is raised
) (
      input  logic                   i_clk
    , input  logic                   i_rst
    // Write interface
    , input  logic [WIDTH-1:0]       i_wr_data
    , input  logic                   i_wr_push
    // Read interface
    , output logic [WIDTH-1:0]       o_rd_data
    , input  logic                   i_rd_pop
    // Status
    , output logic [$clog2(DEPTH):0] o_level
    , output logic                   o_empty
    , output logic                   o_full
);

// Parameters and constants
localparam PTR_W    = $clog2(DEPTH);
localparam PTR_STEP = { {(PTR_W - 1){1'b0}}, 1'b1 };
localparam LVL_STEP = { 1'b0, PTR_STEP };

// Internal state
logic [WIDTH-1:0] data [DEPTH-1:0];
logic [PTR_W-1:0] wr_ptr, rd_ptr;
logic [PTR_W  :0] level;

assign o_rd_data = data[rd_ptr];
assign o_level   = level;
assign o_empty   = (level ==        0);
assign o_full    = (level >= FULL_LVL);

logic truly_full;
assign truly_full = (level == DEPTH);

always @(posedge i_clk, posedge i_rst) begin : p_handle
    if (i_rst) begin
        wr_ptr <= 'd0;
        rd_ptr <= 'd0;
        level  <= 'd0;
    end else begin
        // Pop from FIFO if not empty
        if (i_rd_pop && !o_empty) begin
            rd_ptr <= ((rd_ptr + 'd1) == DEPTH[PTR_W-1:0]) ? 'd0 : (rd_ptr + 'd1);
        end
        // Push to FIFO if not full, or top entry just popped
        if (i_wr_push && (!truly_full || i_rd_pop)) begin
            data[wr_ptr] <= i_wr_data;
            wr_ptr <= ((wr_ptr + 'd1) == DEPTH[PTR_W-1:0]) ? 'd0 : (wr_ptr + 'd1);
        end
        // Update the level
        if (i_wr_push && !i_rd_pop && !truly_full)
            level <= (level + LVL_STEP);
        else if (!i_wr_push && i_rd_pop && !o_empty)
            level <= (level - LVL_STEP);
    end
end

// Aliases for VCD tracing
`ifdef sim_icarus
generate
    genvar idx;
    for (idx = 0; idx < DEPTH; idx = (idx + 1)) begin
        wire [WIDTH-1:0] data_alias = data[idx];
    end
endgenerate
`endif // sim_icarus

endmodule : nx_fifo
