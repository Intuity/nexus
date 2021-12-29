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

// nx_control
// Nexus top-level controller. Responsible for monitoring the mesh, generating
// tick events, and providing feedback to the host.
//
module nx_control
import NXConstants::*;
#(
      parameter ROWS      =  3
    , parameter COLUMNS   =  3
    , parameter INPUTS    = 32
    , parameter OUTPUTS   = 32
    , parameter REGISTERS = 16
) (
      input  logic                         i_clk
    , input  logic                         i_rst
    // Soft reset request
    , output logic                         o_soft_reset
    // Host message streams
    // - Inbound
    , input  control_request_t             i_ctrl_in_data
    , input  logic                         i_ctrl_in_valid
    , output logic                         o_ctrl_in_ready
    // - Outbound
    , output control_response_t            o_ctrl_out_data
    , output logic                         o_ctrl_out_valid
    , input  logic                         i_ctrl_out_ready
    // Mesh message streams
    // - Inbound
    , output node_message_t                o_mesh_in_data
    , output logic                         o_mesh_in_valid
    , input  logic                         i_mesh_in_ready
    // - Outbound
    , input  node_message_t                i_mesh_out_data
    , input  logic                         i_mesh_out_valid
    , output logic                         o_mesh_out_ready
    // Externally visible status
    , output logic                         o_status_active
    , output logic                         o_status_idle
    , output logic                         o_status_trigger
    // Interface to the mesh
    , input  logic [COLUMNS-1:0]           i_mesh_node_idle
    , input  logic                         i_mesh_agg_idle
    , output logic [COLUMNS-1:0]           o_mesh_trigger
    , input  logic [(COLUMNS*OUTPUTS)-1:0] i_mesh_outputs
);

// =============================================================================
// Constants
// =============================================================================

localparam MESH_OUTPUTS     = COLUMNS * OUTPUTS;
localparam MAX_OUTPUT_INDEX = (MESH_OUTPUTS + OUT_BITS_PER_MSG - 1) / OUT_BITS_PER_MSG;
localparam OUTPUT_IDX_WIDTH = 1 + ((MESH_OUTPUTS > OUT_BITS_PER_MSG) ? $clog2(MAX_OUTPUT_INDEX) : 0);

typedef enum logic [1:0] {
      CTRL_IDLE    // 0: Quiescent state (mesh and controller idle)
    , CTRL_ACTIVE  // 1: Controller active, trigger sent, waiting for mesh idle
    , CTRL_OUTPUTS // 2: Generating output messages
    , CTRL_MEMMORY // 3: Handling memory accesses
} ctrl_state_t;

// =============================================================================
// Internal Signals and State
// =============================================================================

// FSM
`DECLARE_DQT(ctrl_state_t, state, i_clk, i_rst, CTRL_IDLE)

// Control request handling
`DECLARE_DQ (             1, soft_reset,    i_clk, i_rst, 'd0)
`DECLARE_DQ (   TIMER_WIDTH, interval,      i_clk, i_rst, 'd0)
`DECLARE_DQ (       COLUMNS, trigger_mask,  i_clk, i_rst, 'd0)
`DECLARE_DQ (             1, active,        i_clk, i_rst, 'd0)
`DECLARE_DQT(node_message_t, mesh_in_data,  i_clk, i_rst, 'd0)
`DECLARE_DQ (             1, mesh_in_valid, i_clk, i_rst, 'd0)

logic              ctrl_req;
control_req_type_t ctrl_cmd;
logic              req_rd_params, req_rd_status, req_soft_rst, req_trigger,
                   req_to_mesh;
logic              mesh_in_stall;

// Control response generation
`DECLARE_DQT(control_response_t, ctrl_out_data,  i_clk, i_rst, 'd0)
`DECLARE_DQ (1,                  ctrl_out_valid, i_clk, i_rst, 'd0)

logic                         ctrl_out_stall;
control_response_parameters_t resp_params;
control_response_status_t     resp_status;
control_response_outputs_t    resp_outputs;
control_response_from_mesh_t  resp_mesh;

// Trigger generation
`DECLARE_DQ(      1, first_tick,    i_clk, i_rst, 'd1)
`DECLARE_DQ(      1, seen_idle_low, i_clk, i_rst, 'd0)
`DECLARE_DQ(      1, all_idle,      i_clk, i_rst, 'd1)
`DECLARE_DQ(      1, trigger,       i_clk, i_rst, 'd0)
`DECLARE_DQ(COLUMNS, trigger_cols,  i_clk, i_rst, 'd0)

// Cycle counting
`DECLARE_DQ(TIMER_WIDTH, cycle, i_clk, i_rst, 'd0)

// Output generation
`DECLARE_DQ(OUTPUT_IDX_WIDTH, out_idx, i_clk, i_rst, 'd0)

logic emit_output_msg;

// Drive soft reset request
assign o_soft_reset = soft_reset_q;

// =============================================================================
// FSM
// =============================================================================

// Coalesce idle signals
assign all_idle = (&i_mesh_node_idle) && i_mesh_agg_idle;

// Manage state transitions
always_comb begin : comb_fsm
    // Initialise
    `INIT_D(state);
    `INIT_D(out_idx);

    // State transitions
    case (state_q)
        // IDLE: Quiescent state waiting for activation
        CTRL_IDLE : begin
            if (active_q) begin
                state = CTRL_ACTIVE;
            end
        end
        // ACTIVE: Trigger sent, mesh active, waiting for idle
        CTRL_ACTIVE : begin
            if (seen_idle_low_q && all_idle_q) begin
                state = CTRL_OUTPUTS;
            end
        end
        // OUTPUTS: Generating output messages
        CTRL_OUTPUTS : begin
            if (!ctrl_out_stall) begin
                // If on the final output message
                if (out_idx_q == MAX_OUTPUT_INDEX[OUTPUT_IDX_WIDTH-1:0]) begin
                    // Reset the output index
                    out_idx = 'd0;
                    // If still ticking go to ACTIVE, otherwise go to IDLE
                    if (active_q) state = CTRL_ACTIVE;
                    else          state = CTRL_IDLE;

                // Otherwise count up
                end else begin
                    out_idx = (out_idx_q + 'd1);
                end
            end
        end
        // Default: Return to IDLE
        default: begin
            state = CTRL_IDLE;
        end
    endcase
end

// =============================================================================
// Trigger Generation
// =============================================================================

// Generate trigger on transition into ACTIVE
assign trigger        = (state_q != CTRL_ACTIVE) && (state == CTRL_ACTIVE);
assign trigger_cols   = {COLUMNS{trigger}} & trigger_mask_q;
assign o_mesh_trigger = trigger_cols_q;

// Monitor for idle going low after trigger
assign seen_idle_low = trigger ? 'd0 : (seen_idle_low_q || !all_idle_q);

// Track the very first tick
assign first_tick = first_tick_q && !trigger;

// =============================================================================
// Cycle Counter
// =============================================================================

assign cycle = cycle_q + ((state_q == CTRL_OUTPUTS && state != CTRL_OUTPUTS) ? 'd1 : 'd0);

// =============================================================================
// Control Request Handling
// =============================================================================

// Qualify request
assign ctrl_req = i_ctrl_in_valid && o_ctrl_in_ready;

// Extract command
assign ctrl_cmd = i_ctrl_in_data.raw.command;

// Decode
assign req_rd_params = ctrl_req && (ctrl_cmd == CONTROL_REQ_TYPE_READ_PARAMS);
assign req_rd_status = ctrl_req && (ctrl_cmd == CONTROL_REQ_TYPE_READ_STATUS);
assign req_soft_rst  = ctrl_req && (ctrl_cmd == CONTROL_REQ_TYPE_SOFT_RESET );
assign req_trigger   = ctrl_req && (ctrl_cmd == CONTROL_REQ_TYPE_TRIGGER    );
assign req_to_mesh   = ctrl_req && (ctrl_cmd == CONTROL_REQ_TYPE_TO_MESH    );

// Trigger reset
assign soft_reset = req_soft_rst || soft_reset_q;

// Capture column triggering mask
assign trigger_mask = req_trigger ? i_ctrl_in_data.trigger.col_mask[COLUMNS-1:0]
                                  : trigger_mask_q;

// Set interval on request, count down on trigger if greater than 0
assign interval = req_trigger                   ? i_ctrl_in_data.trigger.cycles :
                  (trigger && interval_q > 'd0) ? (interval_q - 'd1)
                                                : interval_q;

// Set active on request, deactivate on trigger if interval is 1
assign active = req_trigger                    ? i_ctrl_in_data.trigger.active :
                (trigger && interval_q == 'd1) ? 'd0
                                               : active_q;

// Forward messages into the mesh
assign mesh_in_stall = mesh_in_valid_q && !i_mesh_in_ready;
assign mesh_in_data  = mesh_in_stall ? mesh_in_data_q : i_ctrl_in_data.to_mesh.message;
assign mesh_in_valid = mesh_in_stall || req_to_mesh;

assign o_mesh_in_data  = mesh_in_data_q;
assign o_mesh_in_valid = mesh_in_valid_q;

// Drive ready signal
assign o_ctrl_in_ready = !ctrl_out_stall && !mesh_in_stall && (state_q != CTRL_OUTPUTS);

// =============================================================================
// Control Response Generation
// =============================================================================

// Pad outputs with zeroes up to the next 96 bit boundary
localparam FULL_WIDTH = MAX_OUTPUT_INDEX * OUT_BITS_PER_MSG;
localparam OUTPUT_PAD = FULL_WIDTH - MESH_OUTPUTS;
logic [FULL_WIDTH-1:0] padded_outputs;
assign padded_outputs = { {OUTPUT_PAD{1'b0}}, i_mesh_outputs };

// Populate output response
assign emit_output_msg = (state_q == CTRL_OUTPUTS) && (state == CTRL_OUTPUTS);

always_comb begin : comb_outputs
    resp_outputs.format = CONTROL_RESP_TYPE_OUTPUTS;
    resp_outputs.stamp  = cycle_q;
    resp_outputs.index  = { {(MAX_OUT_IDX_WIDTH-OUTPUT_IDX_WIDTH){1'b0}}, out_idx_q };
    resp_outputs._padding_0 = 'd0;
    for (int idx = 0; idx < MAX_OUTPUT_INDEX; idx++) begin : gen_outputs
        if (out_idx_q == idx[OUTPUT_IDX_WIDTH-1:0]) begin
            assign resp_outputs.section = padded_outputs[idx*OUT_BITS_PER_MSG+:OUT_BITS_PER_MSG];
        end
    end
end

// Populate forwarded mesh response
assign resp_mesh.format     = CONTROL_RESP_TYPE_FROM_MESH;
assign resp_mesh.message    = i_mesh_out_data;
assign resp_mesh._padding_0 = 'd0;
assign o_mesh_out_ready     = !ctrl_out_stall && (state_q != CTRL_OUTPUTS);

// Populate parameter response
assign resp_params.format      = CONTROL_RESP_TYPE_PARAMS;
assign resp_params.id          = HW_DEV_ID;
assign resp_params.ver_major   = HW_VER_MAJOR;
assign resp_params.ver_minor   = HW_VER_MINOR;
assign resp_params.timer_width = TIMER_WIDTH;
assign resp_params.rows        = ROWS[$clog2(MAX_ROW_COUNT)-1:0];
assign resp_params.columns     = COLUMNS[$clog2(MAX_COLUMN_COUNT)-1:0];
assign resp_params.node_ins    = INPUTS[$clog2(MAX_NODE_INPUTS)-1:0];
assign resp_params.node_outs   = OUTPUTS[$clog2(MAX_NODE_OUTPUTS)-1:0];
assign resp_params.node_regs   = REGISTERS[$clog2(MAX_NODE_REGISTERS)-1:0];
assign resp_params._padding_0  = 'd0;

// Populate status response
assign resp_status.format     = CONTROL_RESP_TYPE_STATUS;
assign resp_status.active     = active_q;
assign resp_status.mesh_idle  = &i_mesh_node_idle;
assign resp_status.agg_idle   = i_mesh_agg_idle;
assign resp_status.seen_low   = seen_idle_low_q;
assign resp_status.first_tick = first_tick_q;
assign resp_status.cycle      = cycle_q;
assign resp_status.countdown  = interval_q;
assign resp_status._padding_0 = 'd0;

// Determine when to hold the response
assign ctrl_out_stall = ctrl_out_valid_q && !i_ctrl_out_ready;

// Mux between responses
assign ctrl_out_data = ctrl_out_stall   ? ctrl_out_data_q :
                       emit_output_msg  ? resp_outputs    :
                       i_mesh_out_valid ? resp_mesh       :
                       req_rd_params    ? resp_params     :
                       req_rd_status    ? resp_status
                                        : 'd0;

// Drive the valid
assign ctrl_out_valid = (
    ctrl_out_stall   ||
    req_rd_params   ||
    req_rd_status   ||
    emit_output_msg ||
    i_mesh_out_valid
);

// Drive the ports
assign o_ctrl_out_data  = ctrl_out_data_q;
assign o_ctrl_out_valid = ctrl_out_valid_q;

// =============================================================================
// Debug Status Flags
// =============================================================================

assign o_status_active  = (state_q != CTRL_IDLE);
assign o_status_idle    = all_idle_q;
assign o_status_trigger = trigger_q;

endmodule : nx_control
