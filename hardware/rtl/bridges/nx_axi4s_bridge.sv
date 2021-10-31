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

// nx_axi4s_bridge
// Bidirectional AXI4-Stream to Nexus message stream
//
module nx_axi4s_bridge
import NXConstants::*;
#(
    parameter AXI4_DATA_WIDTH = 64
) (
      input  logic                      i_clk
    , input  logic                      i_rst
    // Inbound AXI4-stream
    , input  wire [AXI4_DATA_WIDTH-1:0] i_ib_axi4s_tdata
    , input  wire                       i_ib_axi4s_tlast
    , input  wire                       i_ib_axi4s_tvalid
    , output wire                       o_ib_axi4s_tready
    // Outbound Nexus message stream
    , output node_message_t             o_ob_nx_data
    , output logic                      o_ob_nx_valid
    , input  logic                      i_ob_nx_ready
    // Inbound Nexus message stream
    , input  node_message_t             i_ib_nx_data
    , input  logic                      i_ib_nx_valid
    , output logic                      o_ib_nx_ready
    // Outbound AXI4-stream
    , output wire [AXI4_DATA_WIDTH-1:0] o_ob_axi4s_tdata
    , output wire                       o_ob_axi4s_tlast
    , output wire                       o_ob_axi4s_tvalid
    , input  wire                       i_ob_axi4s_tready
);

// =============================================================================
// Constants
// =============================================================================

localparam SLOT_WIDTH  = MESSAGE_WIDTH + 1;
localparam A2N_RATIO   = AXI4_DATA_WIDTH / SLOT_WIDTH;
localparam A2N_RATIO_W = $clog2(A2N_RATIO);

// =============================================================================
// Inbound Pathway
// =============================================================================

logic [AXI4_DATA_WIDTH-1:0] axi4s_data;
logic                       axi4s_empty, axi4s_full, axi4s_push, axi4s_pop;

assign axi4s_push = i_ib_axi4s_tvalid && !axi4s_full;

nx_fifo #(
      .DEPTH     ( 2                )
    , .WIDTH     ( AXI4_DATA_WIDTH  )
) axi4s_fifo (
      .i_clk     ( i_clk            )
    , .i_rst     ( i_rst            )
    // Write interface
    , .i_wr_data ( i_ib_axi4s_tdata )
    , .i_wr_push ( axi4s_push       )
    // Read interface
    , .o_rd_data ( axi4s_data       )
    , .i_rd_pop  ( axi4s_pop        )
    // Status
    , .o_level   (                  )
    , .o_empty   ( axi4s_empty      )
    , .o_full    ( axi4s_full       )
);

assign o_ib_axi4s_tready = !axi4s_full;

// MSB of each slot is a presence indicator
logic [A2N_RATIO-1:0] ib_slot_present;
node_message_t        ib_message [A2N_RATIO-1:0];
generate
for (genvar i = 0; i < A2N_RATIO; i = (i + 1)) begin
    assign ib_slot_present[i] = axi4s_data[(i + 1)*SLOT_WIDTH - 1];
    assign ib_message[i]      = axi4s_data[i*SLOT_WIDTH +: MESSAGE_WIDTH];
end
endgenerate

// Create state for output ports
`DECLARE_DQ (A2N_RATIO_W,    ob_nx_slot,  i_clk, i_rst, {A2N_RATIO_W{1'b0}})
`DECLARE_DQT(node_message_t, ob_nx_data,  i_clk, i_rst, {MESSAGE_WIDTH{1'b0}})
`DECLARE_DQ (1,              ob_nx_valid, i_clk, i_rst, 1'b0)

assign o_ob_nx_data  = ob_nx_data_q;
assign o_ob_nx_valid = ob_nx_valid_q;

// Decoding process
always_comb begin : p_inbound
    `INIT_D(ob_nx_slot);
    `INIT_D(ob_nx_data);
    `INIT_D(ob_nx_valid);

    // Default pop to false
    axi4s_pop = 1'b0;

    // Clear valid if acknowledged
    if (i_ob_nx_ready) ob_nx_valid = 1'b0;

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

logic [MESSAGE_WIDTH-1:0] nx_fifo_data;
logic [              1:0] nx_fifo_lvl;
logic                     nx_fifo_empty, nx_fifo_full, nx_fifo_push, nx_fifo_pop;

assign nx_fifo_push = i_ib_nx_valid && !nx_fifo_full;

nx_fifo #(
      .DEPTH     ( 2             )
    , .WIDTH     ( MESSAGE_WIDTH )
) u_nx_fifo (
      .i_clk     ( i_clk         )
    , .i_rst     ( i_rst         )
    // Write interface
    , .i_wr_data ( i_ib_nx_data  )
    , .i_wr_push ( nx_fifo_push  )
    // Read interface
    , .o_rd_data ( nx_fifo_data  )
    , .i_rd_pop  ( nx_fifo_pop   )
    // Status
    , .o_level   ( nx_fifo_lvl   )
    , .o_empty   ( nx_fifo_empty )
    , .o_full    ( nx_fifo_full  )
);

assign o_ib_nx_ready = !nx_fifo_full;

// Create state for output ports
`DECLARE_DQT_ARRAY(node_message_t, A2N_RATIO, ob_axi4s_slot_data,  i_clk, i_rst, {MESSAGE_WIDTH{1'b0}})
`DECLARE_DQ_ARRAY (1,              A2N_RATIO, ob_axi4s_slot_valid, i_clk, i_rst, 1'b0)
`DECLARE_DQ       (A2N_RATIO,                 ob_axi4s_slot,       i_clk, i_rst, {A2N_RATIO_W{1'b0}})
`DECLARE_DQ       (1,                         ob_axi4s_tlast,      i_clk, i_rst, 1'b0)
`DECLARE_DQ       (1,                         ob_axi4s_tvalid,     i_clk, i_rst, 1'b0)

generate
for (genvar i = 0; i < A2N_RATIO; i = (i + 1)) begin
    assign o_ob_axi4s_tdata[(i+1)*SLOT_WIDTH-1]            = ob_axi4s_slot_valid_q[i];
    assign o_ob_axi4s_tdata[i*SLOT_WIDTH +: MESSAGE_WIDTH] = ob_axi4s_slot_data_q[i];
end
endgenerate

assign o_ob_axi4s_tlast  = ob_axi4s_tlast_q;
assign o_ob_axi4s_tvalid = ob_axi4s_tvalid_q;

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
    if (i_ob_axi4s_tready && ob_axi4s_tvalid) begin
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
        ob_axi4s_tlast = (nx_fifo_lvl == 2'd1 && !i_ib_nx_valid);

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
