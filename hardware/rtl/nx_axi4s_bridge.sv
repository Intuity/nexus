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
`include "nx_constants.svh"

// nx_axi4s_bridge
// AXI4-Stream to Nexus message stream
//
module nx_axi4s_bridge #(
    parameter AXI4_DATA_WIDTH = 64
) (
      input  logic clk_i
    , input  logic rst_i
    // Inbound AXI4-stream
    , input  wire [AXI4_DATA_WIDTH-1:0] ib_axi4s_tdata_i
    , input  wire                       ib_axi4s_tlast_i
    , input  wire                       ib_axi4s_tvalid_i
    , output wire                       ib_axi4s_tready_o
    // Outbound Nexus message stream
    , output nx_message_t ob_nx_data_o
    , output logic        ob_nx_valid_o
    , input  logic        ob_nx_ready_i
    // Inbound Nexus message stream
    , input  nx_message_t ib_nx_data_i
    , input  logic        ib_nx_valid_i
    , output logic        ib_nx_ready_o
    // Outbound AXI4-stream
    , output wire [AXI4_DATA_WIDTH-1:0] ob_axi4s_tdata_o
    , output wire                       ob_axi4s_tlast_o
    , output wire                       ob_axi4s_tvalid_o
    , input  wire                       ob_axi4s_tready_i
);

localparam MSG_WIDTH   = $bits(nx_message_t);
localparam SLOT_WIDTH  = MSG_WIDTH + 1;
localparam A2N_RATIO   = AXI4_DATA_WIDTH / SLOT_WIDTH;
localparam A2N_RATIO_W = $clog2(A2N_RATIO);

// =============================================================================
// Inbound Pathway
// =============================================================================

logic [AXI4_DATA_WIDTH-1:0] axi4s_data;
logic                       axi4s_empty, axi4s_full, axi4s_pop;

nx_fifo #(
      .DEPTH(              2)
    , .WIDTH(AXI4_DATA_WIDTH)
) axi4s_fifo (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Write interface
    , .wr_data_i(ib_axi4s_tdata_i)
    , .wr_push_i(ib_axi4s_tvalid_i && !axi4s_full)
    // Read interface
    , .rd_data_o(axi4s_data)
    , .rd_pop_i (axi4s_pop )
    // Status
    , .level_o(           )
    , .empty_o(axi4s_empty)
    , .full_o (axi4s_full )
);

assign ib_axi4s_tready_o = !axi4s_full;

// MSB of each slot is a presence indicator
logic [A2N_RATIO-1:0] ib_slot_present;
nx_message_t          ib_message [A2N_RATIO-1:0];
generate
for (genvar i = 0; i < A2N_RATIO; i = (i + 1)) begin
    assign ib_slot_present[i] = axi4s_data[(i + 1)*SLOT_WIDTH - 1];
    assign ib_message[i]      = axi4s_data[i*SLOT_WIDTH +: MSG_WIDTH];
end
endgenerate

// Create state for output ports
`DECLARE_DQ (A2N_RATIO_W,  ob_nx_slot,  clk_i, rst_i, {A2N_RATIO_W{1'b0}})
`DECLARE_DQT(nx_message_t, ob_nx_data,  clk_i, rst_i, {$bits(nx_message_t){1'b0}})
`DECLARE_DQ (1,            ob_nx_valid, clk_i, rst_i, 1'b0)

assign ob_nx_data_o  = ob_nx_data_q;
assign ob_nx_valid_o = ob_nx_valid_q;

// Decoding process
always_comb begin : p_inbound
    `INIT_D(ob_nx_slot);
    `INIT_D(ob_nx_data);
    `INIT_D(ob_nx_valid);

    // Default pop to false
    axi4s_pop = 1'b0;

    // Clear valid if acknowledged
    if (ob_nx_ready_i) ob_nx_valid = 1'b0;

    // If valid clear, decode the next packet
    if (!ob_nx_valid && !axi4s_empty) begin
        // Forward this slot into the design
        ob_nx_data  = ib_message[ob_nx_slot];
        ob_nx_valid = ib_slot_present[ob_nx_slot];

        // Increment the active slot
        ob_nx_slot = ob_nx_slot + { {(A2N_RATIO_W-1){1'b0}}, 1'b1 };

        // If this entry is exhausted, pop and move on
        if (
            ob_nx_slot_q == (A2N_RATIO - 1) ||
            (ib_slot_present >> ob_nx_slot) == {A2N_RATIO{1'b0}}
        ) begin
            axi4s_pop  = 1'b1;
            ob_nx_slot = {A2N_RATIO_W{1'b0}};
        end
    end
end

// =============================================================================
// Outbound Pathway
// =============================================================================

logic [MSG_WIDTH-1:0] nx_fifo_data;
logic [          1:0] nx_fifo_lvl;
logic                 nx_fifo_empty, nx_fifo_full, nx_fifo_pop;

nx_fifo #(
      .DEPTH(        2)
    , .WIDTH(MSG_WIDTH)
) nx_fifo (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Write interface
    , .wr_data_i(ib_nx_data_i)
    , .wr_push_i(ib_nx_valid_i && !nx_fifo_full)
    // Read interface
    , .rd_data_o(nx_fifo_data)
    , .rd_pop_i (nx_fifo_pop )
    // Status
    , .level_o(nx_fifo_lvl  )
    , .empty_o(nx_fifo_empty)
    , .full_o (nx_fifo_full )
);
assign ib_nx_ready_o = !nx_fifo_full;

// Create state for output ports
`DECLARE_DQT_ARRAY(nx_message_t, A2N_RATIO, ob_axi4s_slot_data,  clk_i, rst_i, {MSG_WIDTH{1'b0}})
`DECLARE_DQ_ARRAY (1,            A2N_RATIO, ob_axi4s_slot_valid, clk_i, rst_i, 1'b0)
`DECLARE_DQ       (A2N_RATIO,               ob_axi4s_slot,       clk_i, rst_i, {A2N_RATIO_W{1'b0}})
`DECLARE_DQ       (1,                       ob_axi4s_tlast,      clk_i, rst_i, 1'b0)
`DECLARE_DQ       (1,                       ob_axi4s_tvalid,     clk_i, rst_i, 1'b0)

generate
for (genvar i = 0; i < A2N_RATIO; i = (i + 1)) begin
    assign ob_axi4s_tdata_o[(i+1)*SLOT_WIDTH-1]        = ob_axi4s_slot_valid_q[i];
    assign ob_axi4s_tdata_o[i*SLOT_WIDTH +: MSG_WIDTH] = ob_axi4s_slot_data_q[i];
end
endgenerate

assign ob_axi4s_tlast_o  = ob_axi4s_tlast_q;
assign ob_axi4s_tvalid_o = ob_axi4s_tvalid_q;

// Encoding process
always_comb begin : p_encode
    int idx;

    `INIT_D_ARRAY(ob_axi4s_slot_data);
    `INIT_D_ARRAY(ob_axi4s_slot_valid);
    `INIT_D(ob_axi4s_slot);
    `INIT_D(ob_axi4s_tlast);
    `INIT_D(ob_axi4s_tvalid);

    // Default pop to false
    nx_fifo_pop = 1'b0;

    // Clear valid if accepted
    if (ob_axi4s_tready_i && ob_axi4s_tvalid) begin
        ob_axi4s_tlast  = 1'b0;
        ob_axi4s_tvalid = 1'b0;
        for (idx = 0; idx < A2N_RATIO; idx = (idx + 1)) begin
            ob_axi4s_slot_data[idx]  = {SLOT_WIDTH{1'b0}};
            ob_axi4s_slot_valid[idx] = 1'b0;
        end
    end

    // If valid clear, encode the next packet
    if (!ob_axi4s_tvalid && !nx_fifo_empty) begin
        // Populate the next slot
        ob_axi4s_slot_data[ob_axi4s_slot]  = nx_fifo_data;
        ob_axi4s_slot_valid[ob_axi4s_slot] = 1'b1;

        // If FIFO emptied, raise TLAST
        ob_axi4s_tlast = (nx_fifo_lvl == 2'd1 && !ib_nx_valid_i);

        // Increment the active slot
        ob_axi4s_slot = ob_axi4s_slot + { {(A2N_RATIO_W-1){1'b0}}, 1'b1 };

        // Pop the FIFO
        nx_fifo_pop = 1'b1;

        // If data filled or TLAST high, mark valid
        if ((ob_axi4s_slot_q == (A2N_RATIO - 1)) || ob_axi4s_tlast) begin
            ob_axi4s_tvalid = 1'b1;
            ob_axi4s_slot    = {A2N_RATIO_W{1'b0}};
        end
    end
end

endmodule : nx_axi4s_bridge
