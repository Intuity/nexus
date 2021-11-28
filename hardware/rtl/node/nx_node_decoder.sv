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

// nx_node_decoder
// Decode messages and maintain the state of inputs to the node, this includes
// configuration parameters and the loopback mask.
//
module nx_node_decoder
import NXConstants::*;
#(
      parameter INPUTS     = 32
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic                        i_clk
    , input  logic                        i_rst
    // Control signals
    , output logic                        o_idle
    // Inbound message stream
    , input  node_message_t               i_msg_data
    , input  logic                        i_msg_valid
    , output logic                        o_msg_ready
    // Write interface to node's memory (driven by node_load_t)
    , output logic [RAM_ADDR_W-1:0]       o_ram_addr
    , output logic [RAM_DATA_W-1:0]       o_ram_wr_data
    , output logic                        o_ram_wr_en
    // Input signal state (driven by node_signal_t)
    , output logic [$clog2(INPUTS)-1:0]   o_input_index
    , output logic                        o_input_value
    , output logic                        o_input_is_seq
    , output logic                        o_input_update
    // Control parameters (driven by node_control_t)
    , output logic [NODE_PARAM_WIDTH-1:0] o_num_instr
    , output logic [INPUTS-1:0]           o_loopback_mask
    , output logic                        o_trace_en
);

// =============================================================================
// Internal signals and state
// =============================================================================

// Message type decode
logic is_msg_load, is_msg_signal, is_msg_control;

// Node memory loading
`DECLARE_DQ(RAM_ADDR_W,     load_address, i_clk, i_rst, 'd0)
`DECLARE_DQ(LOAD_SEG_WIDTH, load_segment, i_clk, i_rst, 'd0)

// Control parameters
logic is_ctrl_instr, is_ctrl_lb, is_ctrl_trace;
`DECLARE_DQ(NODE_PARAM_WIDTH, ctrl_num_instr, i_clk, i_rst, 'd0)
`DECLARE_DQ(INPUTS,           ctrl_lb_mask,   i_clk, i_rst, 'd0)
`DECLARE_DQ(1,                ctrl_trace_en,  i_clk, i_rst, 'd0)

// =============================================================================
// Control signals
// =============================================================================

// Idle unless a valid signal is presented
assign o_idle = !i_msg_valid;

// Tie ready permanently high (messages always consumed in a single cycle)
assign o_msg_ready = 'b1;

// =============================================================================
// Identify message type
// =============================================================================

assign is_msg_load    = i_msg_valid && o_msg_ready && (i_msg_data.raw.header.command == NODE_COMMAND_LOAD    );
assign is_msg_signal  = i_msg_valid && o_msg_ready && (i_msg_data.raw.header.command == NODE_COMMAND_SIGNAL  );
assign is_msg_control = i_msg_valid && o_msg_ready && (i_msg_data.raw.header.command == NODE_COMMAND_CONTROL );

// =============================================================================
// Load command handling
// =============================================================================

// Construct the output (only write on the 'last' load)
assign o_ram_addr    = load_address_q;
assign o_ram_wr_data = { load_segment_q, i_msg_data.load.data };
assign o_ram_wr_en   = is_msg_load && i_msg_data.load.last;

// Increment the address whenever a write is made
assign load_address = load_address_q + (o_ram_wr_en ? 'd1 : 'd0);

// Clear out the held data whenever a write occurs, else pickup the new value
assign load_segment = o_ram_wr_en ? 'd0 :
                      is_msg_load ? i_msg_data.load.data
                                  : load_segment_q;

// =============================================================================
// Signal state handling
// =============================================================================

// Expose to the control block
assign o_input_index  = i_msg_data.signal.index[$clog2(INPUTS)-1:0];
assign o_input_value  = i_msg_data.signal.state;
assign o_input_is_seq = i_msg_data.signal.is_seq;
assign o_input_update = is_msg_signal;

// =============================================================================
// Control parameters
// =============================================================================

// Detect different control writes
assign is_ctrl_instr = (is_msg_control && i_msg_data.control.param == NODE_PARAMETER_INSTRUCTIONS);
assign is_ctrl_lb    = (is_msg_control && i_msg_data.control.param == NODE_PARAMETER_LOOPBACK    );
assign is_ctrl_trace = (is_msg_control && i_msg_data.control.param == NODE_PARAMETER_TRACE       );

// Update held instruction count
assign ctrl_num_instr = (
    is_ctrl_instr ? i_msg_data.control.value : ctrl_num_instr_q
);

// Update loopback mask
assign ctrl_lb_mask = (
    is_ctrl_lb ? { ctrl_lb_mask_q[(INPUTS-NODE_PARAM_WIDTH)-1:0], i_msg_data.control.value }
               : ctrl_lb_mask_q
);

// Update trace enable
assign ctrl_trace_en = (
    is_ctrl_trace ? i_msg_data.control.value[0] : ctrl_trace_en_q
);

// Expose parameters to the control block
assign o_num_instr     = ctrl_num_instr_q;
assign o_loopback_mask = ctrl_lb_mask_q;
assign o_trace_en      = ctrl_trace_en_q;

endmodule : nx_node_decoder
