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

// nx_node_control
// Handles I/O mappings, signal state updates, and generates messages for output
// signal state updates.
//
module nx_node_control
import NXConstants::*;
#(
      parameter INPUTS         =   8 // Number of inputs to each node
    , parameter OUTPUTS        =   8 // Number of outputs from each node
    , parameter OP_STORE_WIDTH = ADDR_ROW_WIDTH + ADDR_COL_WIDTH + IOR_WIDTH + 2
) (
      input  logic clk_i
    , input  logic rst_i
    // Control signals
    , output logic                      idle_o
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
    // External trigger signal
    , input  logic trigger_i
    // Channel tokens
    , input  logic token_grant_i   // Inbound token
    , output logic token_release_o // Outbound token
    // Outbound message stream
    , output node_message_t msg_data_o
    , output logic          msg_valid_o
    , input  logic          msg_ready_i
    // I/O mapping
    , input  logic [     IOR_WIDTH-1:0] map_idx_i     // Which output to configure
    , input  logic [ADDR_ROW_WIDTH-1:0] map_tgt_row_i // Target node's row
    , input  logic [ADDR_COL_WIDTH-1:0] map_tgt_col_i // Target node's column
    , input  logic [     IOR_WIDTH-1:0] map_tgt_idx_i // Target node's input index
    , input  logic                      map_tgt_seq_i // Target node's input is sequential
    , input  logic                      map_valid_i   // Mapping is valid
    // Signal state update
    , input  logic [IOR_WIDTH-1:0] signal_index_i  // Input index
    , input  logic                 signal_is_seq_i // Input is sequential
    , input  logic                 signal_state_i  // Signal state
    , input  logic                 signal_valid_i  // Update is valid
    // Interface to core
    , output logic               core_trigger_o // Start/restart instruction execution
    , output logic [ INPUTS-1:0] core_inputs_o  // Collected input state
    , input  logic [OUTPUTS-1:0] core_outputs_i // Output state from core
    // Interface to memory
    , output logic [$clog2(MAX_NODE_CONFIG)-1:0] store_addr_o    // Output store row address
    , output logic [         OP_STORE_WIDTH-1:0] store_wr_data_o // Output store write data
    , output logic                               store_wr_en_o   // Output store write enable
    , output logic                               store_rd_en_o   // Output store read enable
    , input  logic [         OP_STORE_WIDTH-1:0] store_rd_data_i // Output store read data
);

// TEMP: Token tie-off
assign token_release_o = 1'b1;
logic _unused;
assign _unused = |({1'b1, token_grant_i});

// =============================================================================
// Parameters and constants
// =============================================================================

localparam OP_STORE_ADDR_W = $clog2(MAX_NODE_CONFIG);

// =============================================================================
// Internal state
// =============================================================================

// Output message tracking
`DECLARE_DQ(      OUTPUTS,                  output_actv,  clk_i, rst_i, 'd0)
`DECLARE_DQ_ARRAY(OP_STORE_ADDR_W, OUTPUTS, output_base,  clk_i, rst_i, 'd0)
`DECLARE_DQ_ARRAY(OP_STORE_ADDR_W, OUTPUTS, output_final, clk_i, rst_i, 'd0)
`DECLARE_DQ(      OP_STORE_ADDR_W,          output_next,  clk_i, rst_i, 'd0)

// Node store interface
`DECLARE_DQ(OP_STORE_ADDR_W, store_addr,    clk_i, rst_i, {OP_STORE_ADDR_W{1'b0}})
`DECLARE_DQ(OP_STORE_WIDTH,  store_wr_data, clk_i, rst_i, {OP_STORE_WIDTH{1'b0}})
`DECLARE_DQ(1,               store_wr_en,   clk_i, rst_i, 1'b0)
`DECLARE_DQ(1,               store_rd_en,   clk_i, rst_i, 1'b0)
`DECLARE_DQ(1,               store_rd_resp, clk_i, rst_i, 1'b0)

// Internal loopback
logic [IOR_WIDTH-1:0] loopback_index;
logic                 loopback_state, loopback_valid;

// =============================================================================
// Handle reads and writes to the output message store
// =============================================================================

always_comb begin : p_output_memory
    `INIT_D(output_actv);
    `INIT_D_ARRAY(output_base);
    `INIT_D_ARRAY(output_final);
    `INIT_D(output_next);
    `INIT_D(store_addr);
    `INIT_D(store_wr_data);
    `INIT_D(store_wr_en);
    `INIT_D(store_rd_en);
    `INIT_D(store_rd_resp);

    // Pipeline store_rd_en -> store_rd_resp to align with data return
    store_rd_resp = store_rd_en;

    // Always clear write and read enable
    store_wr_en = 1'b0;
    store_rd_en = 1'b0;

    // When a mapping update arrives, write it into the RAM
    if (map_valid_i) begin
        // Place into the next available slot
        store_addr    = output_next;
        store_wr_en   = 1'b1;
        store_rd_en   = 1'b0;
        store_wr_data = {
              (map_tgt_row_i == node_row_i && map_tgt_col_i == node_col_i) // Loopback?
            , map_tgt_row_i // Target row
            , map_tgt_col_i // Target column
            , map_tgt_idx_i // Target input index
            , map_tgt_seq_i // Target input is sequential
        };
        // If currently inactive, setup the output's base address
        if (!output_actv[map_idx_i]) output_base[map_idx_i] = output_next;
        // Final always tracks
        output_final[map_idx_i] = output_next;
        // Mark this output as active
        output_actv[map_idx_i] = 1'b1;
        // Increment next pointer
        output_next = output_next + 'd1;

    end
end

// =============================================================================
// Handle input updates
// =============================================================================

nx_node_control_inputs #(
      .INPUTS          (INPUTS         )
) ctrl_inputs (
      .clk_i           (clk_i          )
    , .rst_i           (rst_i          )
    // External trigger signal
    , .trigger_i       (trigger_i      )
    // Signal state update
    , .signal_index_i  (signal_index_i )
    , .signal_is_seq_i (signal_is_seq_i)
    , .signal_state_i  (signal_state_i )
    , .signal_valid_i  (signal_valid_i )
    // Loopback interface
    , .loopback_index_i(loopback_index )
    , .loopback_state_i(loopback_state )
    , .loopback_valid_i(loopback_valid )
    // Interface to core
    , .core_trigger_o  (core_trigger_o )
    , .core_inputs_o   (core_inputs_o  )
);

// =============================================================================
// Handle output updates
// =============================================================================

logic [OP_STORE_ADDR_W-1:0] op_rd_addr;
logic                       ctrl_op_idle, op_rd_en;

nx_node_control_outputs #(
      .OUTPUTS          ( OUTPUTS         )
) ctrl_outputs (
      .clk_i            ( clk_i           )
    , .rst_i            ( rst_i           )
    // Status
    , .idle_o           ( ctrl_op_idle    )
    // Interface from core
    , .core_outputs_i   ( core_outputs_i  )
    // Output RAM pointers
    , .output_base_i    ( output_base_q   )
    , .output_final_i   ( output_final_q  )
    , .output_actv_i    ( output_actv_q   )
    // Interface to memory
    , .store_addr_o     ( op_rd_addr      )
    , .store_rd_en_o    ( op_rd_en        )
    , .store_rd_data_i  ( store_rd_data_i )
    // Outbound message stream
    , .msg_data_o       ( msg_data_o      )
    , .msg_valid_o      ( msg_valid_o     )
    , .msg_ready_i      ( msg_ready_i     )
    // Loopback interface
    , .loopback_index_o ( loopback_index  )
    , .loopback_state_o ( loopback_state  )
    , .loopback_valid_o ( loopback_valid  )
);

assign store_addr_o    = op_rd_en ? op_rd_addr : store_addr_q;
assign store_wr_data_o = store_wr_data_q;
assign store_wr_en_o   = store_wr_en_q;
assign store_rd_en_o   = op_rd_en;

// =============================================================================
// Determine if the control block is idle
// =============================================================================

assign idle_o = (ctrl_op_idle && !core_trigger_o);

endmodule : nx_node_control
