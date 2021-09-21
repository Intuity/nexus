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

// nx_node_control_outputs
// Detect output signal state updates
//
module nx_node_control_outputs
import NXConstants::*;
#(
      parameter OUTPUTS      = 32
    , parameter STORE_ADDR_W = $clog2(MAX_NODE_CONFIG)
    , parameter STORE_DATA_W = ADDR_ROW_WIDTH + ADDR_COL_WIDTH + INPUT_WIDTH + 2
) (
      input logic                                  clk_i
    , input logic                                  rst_i
    // Status
    , output logic                                 idle_o
    // Interface from core
    , input  logic [OUTPUTS-1:0]                   core_outputs_i
    // Output RAM pointers
    , input  logic [OUTPUTS-1:0][STORE_ADDR_W-1:0] output_base_i
    , input  logic [OUTPUTS-1:0][STORE_ADDR_W-1:0] output_final_i
    , input  logic [OUTPUTS-1:0]                   output_actv_i
    // Interface to memory
    , output logic [STORE_ADDR_W-1:0]              store_addr_o
    , output logic                                 store_rd_en_o
    , input  logic [STORE_DATA_W-1:0]              store_rd_data_i
    // Outbound message stream
    , output node_message_t                        msg_data_o
    , output logic                                 msg_valid_o
    , input  logic                                 msg_ready_i
    // Loopback interface
    , output logic [IOR_WIDTH-1:0]                 loopback_index_o
    , output logic                                 loopback_state_o
    , output logic                                 loopback_valid_o
);

// =============================================================================
// Internal signals & state
// =============================================================================

// Pipeline stall
logic pipe_stall;

// =============================================================================
// Detect output changes
// =============================================================================

logic [OUTPUTS-1:0] output_xor;
`DECLARE_DQ(OUTPUTS,     output_state,   clk_i, rst_i, 'd0)
`DECLARE_DQ(1,           output_changed, clk_i, rst_i, 'd0)
`DECLARE_DQ(IOR_WIDTH+1, output_index,   clk_i, rst_i, 'd0)
`DECLARE_DQ(1,           output_value,   clk_i, rst_i, 'd0)

// XOR current outputs against tracked state to detect changes
assign output_xor = core_outputs_i ^ output_state;

// OR reduce XOR result to determine if an update needs to be made
assign output_changed = (|output_xor);

// Leading zero count of reversed vector determines which output has changed
nx_clz #(
      .WIDTH         ( OUTPUTS      )
    , .REVERSE_INPUT ( 1'b1         )
) xor_clz (
      .scalar_i      ( output_xor   )
    , .leading_o     ( output_index )
);

// Mux to pickup output value
assign output_value = output_changed ? core_outputs_i[output_index[IOR_WIDTH-1:0]] : 'd0;

// On the last fetch, update the stored state
assign output_state = (output_state_q ^ ({{(OUTPUTS-1){1'b0}},fetch_last} << output_index_q));

// =============================================================================
// Lookup the start and end addresses, and whether the entry is populated
// =============================================================================

logic [STORE_ADDR_W-1:0] pointer_start, pointer_final;
logic                    pointer_valid;

assign pointer_valid = output_changed_q && output_actv_i[output_index_q[OUTPUT_WIDTH-1:0]];
assign pointer_start = output_base_i[output_index_q[OUTPUT_WIDTH-1:0]];
assign pointer_final = output_final_i[output_index_q[OUTPUT_WIDTH-1:0]];

// =============================================================================
// Perform fetch
// =============================================================================

logic fetch_next, fetch_step;

`DECLARE_DQ(STORE_ADDR_W, fetch_address, clk_i, rst_i, 'd0)
`DECLARE_DQ(STORE_ADDR_W, fetch_target,  clk_i, rst_i, 'd0)
`DECLARE_DQ(1,            fetch_active,  clk_i, rst_i, 'd0)
`DECLARE_DQ(1,            fetch_last,    clk_i, rst_i, 'd0)

assign fetch_next   = (!fetch_active_q || fetch_last_q) && !pipe_stall && pointer_valid;

assign fetch_active = (fetch_active_q && (fetch_address_q != fetch_target_q)) || fetch_next;

assign fetch_step   = fetch_active_q && !pipe_stall;

assign fetch_address = fetch_next ? pointer_start
                                  : (fetch_address_q + (fetch_step ? 'd1 : 'd0));

assign fetch_target  = fetch_next ? pointer_final : fetch_target_q;

assign fetch_last    = fetch_active && (fetch_address == fetch_target);

assign store_addr_o  = fetch_address;
assign store_rd_en_o = fetch_active;

// =============================================================================
// Create delay lines for value and valid to align with fetch
// =============================================================================

`DECLARE_DQ(2, delayed_value, clk_i, rst_i, 'd0)
`DECLARE_DQ(2, delayed_valid, clk_i, rst_i, 'd0)

assign delayed_value = pipe_stall ? delayed_value_q : { delayed_value_q[0], output_value_q };
assign delayed_valid = pipe_stall ? delayed_valid_q : { delayed_valid_q[0], pointer_valid  };

// =============================================================================
// Hold fetch result
// =============================================================================

`DECLARE_DQ(STORE_DATA_W, fetched_data,  clk_i, rst_i, 'd0)
`DECLARE_DQ(1,            fetched_valid, clk_i, rst_i, 'd0)
`DECLARE_DQ(1,            fetched_value, clk_i, rst_i, 'd0)

assign fetched_data  = pipe_stall ? fetched_data_q  : store_rd_data_i;
assign fetched_valid = pipe_stall ? fetched_valid_q : delayed_valid_q[0];
assign fetched_value = pipe_stall ? fetched_value_q : delayed_value_q[0];

// =============================================================================
// Decode fields from the fetched data
// =============================================================================

logic [ADDR_ROW_WIDTH-1:0] msg_row;
logic [ADDR_COL_WIDTH-1:0] msg_col;
logic [   INPUT_WIDTH-1:0] msg_idx;
logic                      msg_lb, msg_seq;

assign { msg_lb, msg_row, msg_col, msg_idx, msg_seq } = fetched_data_q;

// =============================================================================
// Drive loopback
// =============================================================================

assign loopback_index_o = msg_idx;
assign loopback_state_o = fetched_value_q;
assign loopback_valid_o = msg_lb && fetched_valid_q;

// =============================================================================
// Construct outbound message
// =============================================================================

// Hold valid
`DECLARE_DQT(node_sig_state_t, msg_data,  clk_i, rst_i, 'd0)
`DECLARE_DQ (               1, msg_valid, clk_i, rst_i, 'd0)

// Construct the header
node_header_t sig_hdr;
assign sig_hdr.row     = msg_row;
assign sig_hdr.column  = msg_col;
assign sig_hdr.command = NODE_COMMAND_SIG_STATE;

// Construct the message
node_sig_state_t msg_next;
assign msg_next.header     = sig_hdr;
assign msg_next.index      = msg_idx;
assign msg_next.is_seq     = msg_seq;
assign msg_next.state      = fetched_value_q;
assign msg_next._padding_0 = 'd0;

assign msg_data = (!msg_valid_q || msg_ready_i) ? msg_next : msg_data_q;

// Drive the valid
assign msg_valid = (msg_valid_q && !msg_ready_i) || fetched_valid_q;

// Drive outputs
assign msg_data_o  = msg_data_q;
assign msg_valid_o = msg_valid_q;

// Control stall
assign pipe_stall = msg_valid_o && !msg_ready_i;

// =============================================================================
// Determine idle state
// =============================================================================

assign idle_o = !(msg_valid_q || fetched_valid || output_changed);

endmodule : nx_node_control_outputs