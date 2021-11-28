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
// Handles output message generation.
//
module nx_node_control_outputs
import NXConstants::*;
#(
      parameter OUTPUTS    = 32
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic                        i_clk
    , input  logic                        i_rst
    // Control signals
    , input  node_id_t                    i_node_id
    , input  logic                        i_trace_en
    , output logic                        o_idle
    // Inputs from decoder
    , input  logic [NODE_PARAM_WIDTH-1:0] i_num_instr
    // Output message stream
    , output node_message_t               o_msg_data
    , output logic                        o_msg_valid
    , input  logic                        i_msg_ready
    // Interface to store
    , output logic [RAM_ADDR_W-1:0]       o_ram_addr
    , output logic                        o_ram_rd_en
    , input  logic [RAM_DATA_W-1:0]       i_ram_rd_data
    // Interface to logic core
    , input  logic                        i_core_trigger
    , input  logic                        i_core_idle
    , input  logic [OUTPUTS-1:0]          i_core_outputs
);

// =============================================================================
// Constants
// =============================================================================

localparam OUTPUT_WIDTH = $clog2(OUTPUTS) + 1;
localparam TRC_SECTIONS = (OUTPUTS + TRACE_SECTION_WIDTH - 1) / TRACE_SECTION_WIDTH;

typedef enum logic [2:0] { IDLE, LOOKUP, QUERY, SEND, SEND_TRACE } fsm_t;

// =============================================================================
// Internal Signals and State
// =============================================================================

// FSM
`DECLARE_DQT(fsm_t, fsm_state, i_clk, i_rst, IDLE)

logic trace_pend;

// Output change detection
`DECLARE_DQ(OUTPUTS,      outputs_last, i_clk, i_rst, 'd0)
`DECLARE_DQ(OUTPUT_WIDTH, output_index, i_clk, i_rst, 'd0)
`DECLARE_DQ(1,            output_value, i_clk, i_rst, 'd0)
`DECLARE_DQ(1,            any_change,   i_clk, i_rst, 'd0)

logic [OUTPUTS-1:0] output_xor;
logic               output_change;

// RAM interface
`DECLARE_DQT(output_lookup_t, pointers, i_clk, i_rst, 'd0)
`DECLARE_DQ (RAM_ADDR_W,      rd_addr,  i_clk, i_rst, 'd0)
`DECLARE_DQ (1,               last,     i_clk, i_rst, 'd0)

// Signal message generation
output_mapping_t mapping;
node_header_t    sig_hdr;
node_signal_t    sig_data;

// Trace message generation
`DECLARE_DQ(TRACE_SELECT_WIDTH, trc_select, i_clk, i_rst, 'd0)

node_header_t trc_hdr;
node_trace_t  trc_data;

// Message generation
`DECLARE_DQ (1,             msg_valid, i_clk, i_rst, 'd0)
`DECLARE_DQT(node_signal_t, msg_data,  i_clk, i_rst, 'd0)

logic msg_stall;

// =============================================================================
// FSM
// =============================================================================

// Determine if trace needs to be emitted
assign trace_pend = any_change_q && i_trace_en && i_core_idle;

// Determine if the control block is idle
assign o_idle = (fsm_state_q == IDLE) && !output_change && !trace_pend;

// Switch through FSM states
always_comb begin : comb_fsm
    `INIT_D(fsm_state);
    case (fsm_state)
        // IDLE : Waiting for an output signal change
        IDLE : begin
            if      (output_change) fsm_state = LOOKUP;
            else if (trace_pend   ) fsm_state = SEND_TRACE;
        end
        // LOOKUP : Querying the store for the output vector lookup
        LOOKUP : begin
            if (!msg_stall) fsm_state = QUERY;
        end
        // QUERY : Perform the first fetch from the RAM
        QUERY : begin
            // For purely looped-back outputs:
            //   - If another change is detected go straight to LOOKUP
            if      (!pointers.active &&  output_change) fsm_state = LOOKUP;
            //   - Otherwise go to idle
            else if (!pointers.active && !output_change) fsm_state = IDLE;
            // Otherwise move on to SEND
            else                  fsm_state = SEND;
        end
        // SEND : Retrieve and send the stream of output messages
        SEND : begin
            // On the last read go to LOOKUP if another change is detected,
            // otherwise go to idle
            if (last_q && !msg_stall) begin
                if      (output_change) fsm_state = LOOKUP;
                else if (trace_pend   ) fsm_state = SEND_TRACE;
                else                    fsm_state = IDLE;
            end
        end
        // SEND_TRACE : Emit output state trace messages
        SEND_TRACE : begin
            if (!msg_stall && trc_select_q == (TRC_SECTIONS - 1)) fsm_state = IDLE;
        end
        // Default : Return to IDLE state and wait for next cycle
        default begin
            fsm_state = IDLE;
        end
    endcase
end

// =============================================================================
// Detect Output Changes
// =============================================================================

// Detect changes in the output array
assign output_xor    = (i_core_outputs ^ outputs_last_q);
assign output_change = |output_xor;

// Use a leading zero count to determine the output index
nx_clz #(
      .WIDTH         ( OUTPUTS      )
    , .REVERSE_INPUT ( 1'b1         )
) u_clz (
      .i_scalar      ( output_xor   )
    , .o_leading     ( output_index )
);

// Track if any change has occurred this cycle
assign any_change = (
    (i_core_trigger || (fsm_state_q == SEND_TRACE)) ? 'd0 : (any_change_q || output_change)
);

// =============================================================================
// Capture the Updated Output in Lookup
// =============================================================================

assign output_value = (
    (fsm_state_q == LOOKUP && !msg_stall) ? ~outputs_last_q[output_index_q[OUTPUT_WIDTH-2:0]]
                                          : output_value_q
);

// =============================================================================
// Update Held Output State in Lookup
// =============================================================================

generate
for (genvar idx = 0; idx < OUTPUTS; idx++) begin : gen_update_state
    assign outputs_last[idx] = (
        (fsm_state_q == LOOKUP && !msg_stall && output_index_q == idx[OUTPUT_WIDTH-1:0])
            ? ~outputs_last_q[idx] : outputs_last_q[idx]
    );
end
endgenerate

// =============================================================================
// RAM Interface
// =============================================================================

// Determine the read address
always_comb begin : comb_rd_addr
    case ({ fsm_state_q, msg_stall })
        // Lookup is placed immediately after instructions, one entry per output
        { LOOKUP, 1'b0 } : rd_addr = { i_num_instr[RAM_ADDR_W-1:0] + { {(RAM_ADDR_W-OUTPUT_WIDTH){1'b0}}, output_index_q } };
        // In the QUERY state, use the start pointer provided by the RAM
        { QUERY,  1'b0 } : rd_addr = pointers.start;
        // If in SEND, read the next address
        { SEND,   1'b0 } : rd_addr = (rd_addr_q + 'd1);
        // Otherwise hold the same address (could be stalled or inactive)
        default          : rd_addr = rd_addr_q;
    endcase
end

// Drive read request
assign o_ram_rd_en = (fsm_state_q != IDLE);
assign o_ram_addr  = rd_addr;

// Capture lookup result
assign pointers = (fsm_state_q == QUERY) ? i_ram_rd_data[$bits(output_lookup_t)-1:0]
                                         : pointers_q;

// Detect the last fetch
assign last = (rd_addr == pointers.stop);

// =============================================================================
// Generate Signal Messages
// =============================================================================

// Decode RAM response
assign mapping = i_ram_rd_data[$bits(output_mapping_t)-1:0];

// Generate the header
assign sig_hdr.row     = mapping.row;
assign sig_hdr.column  = mapping.column;
assign sig_hdr.command = NODE_COMMAND_SIGNAL;

// Generate the signal message
assign sig_data.header     = sig_hdr;
assign sig_data.index      = mapping.index;
assign sig_data.is_seq     = mapping.is_seq;
assign sig_data.state      = output_value_q;
assign sig_data._padding_0 = 'd0;

// =============================================================================
// Generate Trace Messages
// =============================================================================

// Count up through the trace sections
assign trc_select = (
    (fsm_state_q == SEND_TRACE) ? (trc_select_q + (msg_stall ? 'd0 : 'd1)) : 'd0
);

// Generate the header
assign trc_hdr.row     = i_node_id.row;
assign trc_hdr.column  = i_node_id.column;
assign trc_hdr.command = NODE_COMMAND_TRACE;

// Generate the trace message
always_comb begin : comb_trace
    trc_data = 'd0;
    trc_data.header = trc_hdr;
    trc_data.select = trc_select_q;
    for (int idx = 0; idx < TRC_SECTIONS; idx++) begin
        if (trc_select_q == idx[TRACE_SELECT_WIDTH-1:0]) begin
            trc_data.trace = i_core_outputs[idx*TRACE_SECTION_WIDTH+:TRACE_SECTION_WIDTH];
        end
    end
end

// =============================================================================
// Combine Message Streams
// =============================================================================

// Detect stall condition
assign msg_stall = msg_valid_q && !i_msg_ready;

// Mux between signal and trace messages
assign msg_data = (
    msg_stall ? msg_data_q : ((fsm_state_q == SEND) ? sig_data : trc_data)
);

// Drive message valid high when in SEND
assign msg_valid = (
    (msg_stall && msg_valid_q ) ||
    (fsm_state_q == SEND      ) ||
    (fsm_state_q == SEND_TRACE)
);

// Drive outputs
assign o_msg_data  = msg_data_q;
assign o_msg_valid = msg_valid_q;

endmodule : nx_node_control_outputs
