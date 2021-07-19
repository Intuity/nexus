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

// nx_control
// Nexus top-level controller. Responsible for monitoring the mesh, generating
// tick events, and providing status feedback to the host.
//
module nx_control #(
      parameter ROWS       = 3
    , parameter COLUMNS    = 3
    , parameter INPUTS     = 8
    , parameter OUTPUTS    = 8
    , parameter REGISTERS  = 8
) (
      input  logic clk_i
    , input  logic rst_i
    // Inbound message stream (from host)
    , input  nx_ctrl_req_t inbound_data_i
    , input  logic         inbound_valid_i
    , output logic         inbound_ready_o
    // Outbound message stream (to host)
    , output nx_ctrl_resp_t outbound_data_o
    , output logic          outbound_valid_o
    , input  logic          outbound_ready_i
    // Externally visible status
    , output logic status_active_o  // High when the mesh is active
    , output logic status_idle_o    // High when the mesh goes idle
    , output logic status_trigger_o // Pulses high on every tick every
    // Interface to the mesh
    , input  logic               mesh_idle_i     // High when mesh fully idle
    , output logic               mesh_trigger_o  // Trigger for the next cycle
    , output logic [COLUMNS-1:0] token_grant_o   // Per-column token emit
    , input  logic [COLUMNS-1:0] token_release_i // Per-column token return
);

localparam PYLD_WIDTH = `NX_MESSAGE_WIDTH - $bits(nx_ctrl_command_t);

// Internal state
`DECLARE_DQ(         1, active,         clk_i, rst_i,               1'b0)
`DECLARE_DQ(         1, trigger,        clk_i, rst_i,               1'b0)
`DECLARE_DQ(         1, seen_idle_low,  clk_i, rst_i,               1'b0)
`DECLARE_DQ(         1, first_tick,     clk_i, rst_i,               1'b1)
`DECLARE_DQ(PYLD_WIDTH, cycle,          clk_i, rst_i, {PYLD_WIDTH{1'b0}})
`DECLARE_DQ(PYLD_WIDTH, interval,       clk_i, rst_i, {PYLD_WIDTH{1'b0}})
`DECLARE_DQ(PYLD_WIDTH, interval_count, clk_i, rst_i, {PYLD_WIDTH{1'b0}})
`DECLARE_DQ(         1, interval_set,   clk_i, rst_i,               1'b0)
`DECLARE_DQ(   COLUMNS, token_grant,    clk_i, rst_i,    {COLUMNS{1'b0}})

// Connect outputs
assign status_active_o  = active_q;
assign status_idle_o    = mesh_idle_i;
assign status_trigger_o = trigger_q;

assign mesh_trigger_o = trigger_q;
assign token_grant_o  = token_grant_q;

// Generate cycle triggers
assign trigger = active_q && seen_idle_low_q && mesh_idle_i;

// Monitor for idle going low after each trigger event
assign seen_idle_low = trigger ? 1'b0 : (seen_idle_low_q || !mesh_idle_i);

// Track the first trigger into the mesh
assign first_tick = first_tick_q && !trigger;

// Count active cycles
assign cycle = trigger ? (cycle_q + { {(PYLD_WIDTH-1){1'b0}}, 1'b1 }) : cycle_q;

// Generate token grant signal
assign token_grant = (trigger && first_tick_q) ? {COLUMNS{1'b1}} : token_release_i;

// Outbound message FIFO
nx_message_t send_data;
logic        send_valid, ob_fifo_empty, ob_fifo_full;

assign inbound_ready_o  = !ob_fifo_full;
assign outbound_valid_o = !ob_fifo_empty;

nx_fifo #(
      .DEPTH(                2)
    , .WIDTH(`NX_MESSAGE_WIDTH)
) ob_fifo (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Write interface
    , .wr_data_i(send_data )
    , .wr_push_i(send_valid)
    // Read interface
    , .rd_data_o(outbound_data_o                     )
    , .rd_pop_i (outbound_valid_o && outbound_ready_i)
    // Status
    , .level_o()
    , .empty_o(ob_fifo_empty)
    , .full_o (ob_fifo_full )
);

// Inbound stream decoder
nx_ctrl_payload_param_t    req_pld_param;
nx_ctrl_payload_active_t   req_pld_active;
nx_ctrl_payload_interval_t req_pld_interval;
assign req_pld_param    = inbound_data_i.payload;
assign req_pld_active   = inbound_data_i.payload;
assign req_pld_interval = inbound_data_i.payload;

always_comb begin : p_decode
    // Internal state
    `INIT_D(active);
    `INIT_D(interval);
    `INIT_D(interval_count);
    `INIT_D(interval_set);

    // Initialise variables
    send_data  = 32'd0;
    send_valid =  1'b0;

    // If interval elapsed, deactivate automatically
    if (interval_set && interval_count == interval) begin
        active       = 1'b0;
        interval_set = 1'b0;
    end

    // Increment interval counter on trigger high
    if (trigger_q) begin
        interval_count = interval_count + { {(PYLD_WIDTH-1){1'b0}}, 1'b1 };
    end

    // Handle an incoming message
    if (inbound_valid_i && inbound_ready_o) begin
        case (inbound_data_i.command)
            // Respond with the device identifier (NXS)
            NX_CTRL_ID: begin
                send_data  = { {(`NX_MESSAGE_WIDTH-24){1'b0}}, `NX_DEVICE_ID };
                send_valid = 1'b1;
            end
            // Respond with the major and minor versions of the mesh
            NX_CTRL_VERSION: begin
                send_data  = {
                    {(`NX_MESSAGE_WIDTH-16){1'b0}},
                    `NX_VERSION_MAJOR,
                    `NX_VERSION_MINOR
                };
                send_valid = 1'b1;
            end
            // Respond with the different parameters of the mesh
            NX_CTRL_PARAM: begin
                case (req_pld_param.param)
                    NX_PARAM_COUNTER_WIDTH:
                        send_data = PYLD_WIDTH[PYLD_WIDTH-1:0];
                    NX_PARAM_ROWS:
                        send_data = ROWS[PYLD_WIDTH-1:0];
                    NX_PARAM_COLUMNS:
                        send_data = COLUMNS[PYLD_WIDTH-1:0];
                    NX_PARAM_NODE_INPUTS:
                        send_data = INPUTS[PYLD_WIDTH-1:0];
                    NX_PARAM_NODE_OUTPUTS:
                        send_data = OUTPUTS[PYLD_WIDTH-1:0];
                    NX_PARAM_NODE_REGISTERS:
                        send_data = REGISTERS[PYLD_WIDTH-1:0];
                    default:
                        send_data = {PYLD_WIDTH{1'b0}};
                endcase
                send_valid = 1'b1;
            end
            // Set/clear the active switch for the mesh
            NX_CTRL_ACTIVE: begin
                active = req_pld_active.active;
            end
            // Read back various status flags
            NX_CTRL_STATUS: begin
                send_data = {
                    {(PYLD_WIDTH-4){1'b0}}, active_q, seen_idle_low_q,
                    first_tick_q, interval_set_q
                };
                send_valid = 1'b1;
            end
            // Read back the number of elapsed cycles
            NX_CTRL_CYCLES: begin
                send_data  = cycle_q;
                send_valid = 1'b1;
            end
            // Set/clear the interval (number of cycles to run for)
            NX_CTRL_INTERVAL: begin
                interval       = req_pld_interval.interval;
                interval_count = {PYLD_WIDTH{1'b0}};
                interval_set   = (req_pld_interval.interval != 0);
            end
            // Catch-all
            default: begin
                send_valid = 1'b0;
            end
        endcase
    end
end

endmodule : nx_control
