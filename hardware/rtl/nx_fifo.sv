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

module nx_fifo #(
      parameter DEPTH    =     2 // How many entries in the FIFO
    , parameter WIDTH    =    32 // The width of each FIFO entry
    , parameter FULL_LVL = DEPTH // The level at which the full flag is raised
) (
      input  logic clk
    , input  logic rst
    // Write interface
    , input  logic [WIDTH-1:0] wr_data
    , input  logic             wr_push
    // Read interface
    , output logic [WIDTH-1:0] rd_data
    , input  logic             rd_pop
    // Status
    , output logic [$clog2(DEPTH)-1:0] level
    , output logic                     empty
    , output logic                     full
);

localparam PTR_W    = $clog2(DEPTH);
localparam PTR_STEP = { {PTR_W{1'b0}}, 1'b1 };
localparam LVL_STEP = { 1'b0, PTR_STEP };

logic [WIDTH-1:0] m_data [DEPTH-1:0];
logic [PTR_W-1:0] m_wr_ptr, m_rd_ptr;
logic [PTR_W  :0] m_level;

assign rd_data = m_data[m_rd_ptr];
assign level   = m_level;
assign empty   = (m_level ==        0);
assign full    = (m_level == FULL_LVL);

logic m_truly_full = (m_level == DEPTH);

always @(posedge clk, posedge rst) begin : p_handle
    if (rst) begin
        m_wr_ptr <= {PTR_W{1'b0}};
        m_rd_ptr <= {PTR_W{1'b0}};
        m_level  <= {(PTR_W+1){1'b0}};
    end else begin
        // Pop from FIFO if not empty
        if (rd_pop && !empty) begin
            m_rd_ptr <= (m_rd_ptr + PTR_STEP) % DEPTH;
        end
        // Push to FIFO if not full, or top entry just popped
        if (wr_push && (!m_truly_full || rd_pop)) begin
            m_data[m_wr_ptr] <= wr_data;
            m_wr_ptr         <= (m_wr_ptr + PTR_STEP) % DEPTH;
        end
        // Update the level
        if (wr_push && !rd_pop && !m_truly_full)
            m_level <= (m_level + LVL_STEP);
        else if (!wr_push && rd_pop && !empty)
            m_level <= (m_level - LVL_STEP);
    end
end

// Aliases for VCD tracing
`ifndef SYNTHESIS
generate
    genvar idx;
    for (idx = 0; idx < DEPTH; idx = (idx + 1)) begin : m_alias
        wire [WIDTH-1:0] m_data_alias = m_data[idx];
    end
endgenerate
`endif

endmodule