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

// nx_fifo
// Parameterisable FIFO
//
module nx_fifo #(
      parameter DEPTH    =     2 // How many entries in the FIFO
    , parameter WIDTH    =    32 // The width of each FIFO entry
    , parameter FULL_LVL = DEPTH // The level at which the full flag is raised
) (
      input  logic                   clk_i
    , input  logic                   rst_i
    // Write interface
    , input  logic [      WIDTH-1:0] wr_data_i
    , input  logic                   wr_push_i
    // Read interface
    , output logic [      WIDTH-1:0] rd_data_o
    , input  logic                   rd_pop_i
    // Status
    , output logic [$clog2(DEPTH):0] level_o
    , output logic                   empty_o
    , output logic                   full_o
);

// Parameters and constants
localparam PTR_W    = $clog2(DEPTH);
localparam PTR_STEP = { {PTR_W{1'b0}}, 1'b1 };
localparam LVL_STEP = { 1'b0, PTR_STEP };

// Internal state
logic [WIDTH-1:0] data [DEPTH-1:0];
logic [PTR_W-1:0] wr_ptr, rd_ptr;
logic [PTR_W  :0] level;

assign rd_data_o = data[rd_ptr];
assign level_o   = level;
assign empty_o   = (level ==        0);
assign full_o    = (level == FULL_LVL);

logic truly_full;
assign truly_full = (level == DEPTH);

always @(posedge clk_i, posedge rst_i) begin : p_handle
    if (rst_i) begin
        wr_ptr <= {PTR_W{1'b0}};
        rd_ptr <= {PTR_W{1'b0}};
        level  <= {(PTR_W+1){1'b0}};
    end else begin
        // Pop from FIFO if not empty
        if (rd_pop_i && !empty_o) begin
            rd_ptr <= (
                ((rd_ptr + PTR_STEP) > DEPTH)
                    ? (rd_ptr + PTR_STEP - DEPTH)
                    : (rd_ptr + PTR_STEP)
            );
        end
        // Push to FIFO if not full, or top entry just popped
        if (wr_push_i && (!truly_full || rd_pop_i)) begin
            data[wr_ptr] <= wr_data_i;
            wr_ptr       <= (
                ((wr_ptr + PTR_STEP) > DEPTH)
                    ? (wr_ptr + PTR_STEP - DEPTH)
                    : (wr_ptr + PTR_STEP)
            );
        end
        // Update the level
        if (wr_push_i && !rd_pop_i && !truly_full)
            level <= (level + LVL_STEP);
        else if (!wr_push_i && rd_pop_i && !empty_o)
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

endmodule