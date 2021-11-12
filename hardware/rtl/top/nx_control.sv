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
      parameter ROWS      = 3
    , parameter COLUMNS   = 3
    , parameter INPUTS    = 8
    , parameter OUTPUTS   = 8
    , parameter REGISTERS = 8
) (
      input  logic               i_clk
    , input  logic               i_rst
    // Inbound message stream (from host)
    , input  control_message_t   i_inbound_data
    , input  logic               i_inbound_valid
    , output logic               o_inbound_ready
    // Outbound message stream (to host)
    , output control_response_t  o_outbound_data
    , output logic               o_outbound_valid
    , input  logic               i_outbound_ready
    // Soft reset request
    , output logic               o_soft_reset
    // Externally visible status
    , output logic               o_status_active
    , output logic               o_status_idle
    , output logic               o_status_trigger
    // Interface to the mesh
    , input  logic [COLUMNS-1:0] i_mesh_idle
    , output logic [COLUMNS-1:0] o_mesh_trigger
);

// =============================================================================
// Constants
// =============================================================================

localparam RX_PYLD_WIDTH = MESSAGE_WIDTH - $bits(control_command_t);
localparam TX_PYLD_WIDTH = MESSAGE_WIDTH;

// =============================================================================
// Internal Signals and State
// =============================================================================

// Controller State
`DECLARE_DQ (                 1, soft_reset,     i_clk, i_rst, 'd0)
`DECLARE_DQ (                 1, seen_idle_low,  i_clk, i_rst, 'd0)
`DECLARE_DQ (     RX_PYLD_WIDTH, interval,       i_clk, i_rst, 'd0)
`DECLARE_DQ (     RX_PYLD_WIDTH, interval_count, i_clk, i_rst, 'd0)
`DECLARE_DQ (                 1, interval_set,   i_clk, i_rst, 'd0)
`DECLARE_DQT(control_response_t, send_data,      i_clk, i_rst, 'd0)
`DECLARE_DQ (                 1, send_valid,     i_clk, i_rst, 'd0)
`DECLARE_DQ (                 1, all_idle,       i_clk, i_rst, 'd0)

// Trigger generation
`DECLARE_DQ(      1, active,     i_clk, i_rst, 'd0)
`DECLARE_DQ(      1, first_tick, i_clk, i_rst, 'd1)
`DECLARE_DQ(COLUMNS, trigger,    i_clk, i_rst, 'd0)

// Cycle counter
`DECLARE_DQ(TX_PYLD_WIDTH, cycle, i_clk, i_rst, 'd0)

// Inbound FIFO
control_message_t ib_fifo_data;
logic             ib_fifo_empty, ib_fifo_full, ib_fifo_push, ib_fifo_pop;

// Drive soft reset request
assign o_soft_reset = soft_reset_q;

// =============================================================================
// Inbound Message FIFO
// =============================================================================

// Push when message presented and not full
assign ib_fifo_push = i_inbound_valid && !ib_fifo_full;

// Deassert stream ready when FIFO is full
assign o_inbound_ready = !ib_fifo_full;

nx_fifo #(
      .DEPTH     ( 2              )
    , .WIDTH     ( MESSAGE_WIDTH  )
) u_ib_fifo (
      .i_clk     ( i_clk          )
    , .i_rst     ( i_rst          )
    // Write interface
    , .i_wr_data ( i_inbound_data )
    , .i_wr_push ( ib_fifo_push   )
    // Read interface
    , .o_rd_data ( ib_fifo_data   )
    , .i_rd_pop  ( ib_fifo_pop    )
    // Status
    , .o_level   (                )
    , .o_empty   ( ib_fifo_empty  )
    , .o_full    ( ib_fifo_full   )
);

// =============================================================================
// Message Handling
// =============================================================================

// Drive outputs with send data
assign o_outbound_data  = send_data_q;
assign o_outbound_valid = send_valid_q;

// Perform decode
always_comb begin : comb_decode
    // Internal state
    `INIT_D(soft_reset);
    `INIT_D(active);
    `INIT_D(interval);
    `INIT_D(interval_count);
    `INIT_D(interval_set);
    `INIT_D(send_data);
    `INIT_D(send_valid);

    // Clear pop
    ib_fifo_pop = 1'b0;

    // Clear valid if accepted
    if (i_outbound_ready) send_valid = 1'b0;

    // On counter elapse, deactivate automatically & clear counter for next run
    if (interval_set && interval_count == interval) begin
        active         = 1'b0;
        interval_count = 'd0;
    end

    // Increment interval counter on trigger high
    if (|trigger_q) begin
        interval_count = interval_count + 'd1;
    end

    // Handle an incoming message
    if (!send_valid && !ib_fifo_empty) begin
        // Decode command
        case (ib_fifo_data.raw.command)
            // Respond with the device identifier (NXS)
            CONTROL_COMMAND_ID: begin
                send_valid = 1'b1;
                send_data  = { {(MESSAGE_WIDTH-24){1'b0}}, HW_DEV_ID[23:0] };
            end
            // Respond with the major and minor versions of the mesh
            CONTROL_COMMAND_VERSION: begin
                send_valid = 1'b1;
                send_data  = {
                    {(MESSAGE_WIDTH-16){1'b0}}, HW_VER_MAJOR[7:0], HW_VER_MINOR[7:0]
                };
            end
            // Respond with the different parameters of the mesh
            CONTROL_COMMAND_PARAM: begin
                case (ib_fifo_data.param.param)
                    CONTROL_PARAM_COUNTER_WIDTH:
                        send_data = TX_PYLD_WIDTH[TX_PYLD_WIDTH-1:0];
                    CONTROL_PARAM_ROWS:
                        send_data = ROWS[TX_PYLD_WIDTH-1:0];
                    CONTROL_PARAM_COLUMNS:
                        send_data = COLUMNS[TX_PYLD_WIDTH-1:0];
                    CONTROL_PARAM_NODE_INPUTS:
                        send_data = INPUTS[TX_PYLD_WIDTH-1:0];
                    CONTROL_PARAM_NODE_OUTPUTS:
                        send_data = OUTPUTS[TX_PYLD_WIDTH-1:0];
                    CONTROL_PARAM_NODE_REGISTERS:
                        send_data = REGISTERS[TX_PYLD_WIDTH-1:0];
                    default:
                        send_data = {TX_PYLD_WIDTH{1'b0}};
                endcase
                send_valid = 1'b1;
            end
            // Set/clear the active switch for the mesh
            CONTROL_COMMAND_ACTIVE: begin
                active = ib_fifo_data.active.active;
            end
            // Read back various status flags
            CONTROL_COMMAND_STATUS: begin
                send_valid = 1'b1;
                send_data  = 'd0;
                send_data.status.active       = active_q;
                send_data.status.idle_low     = seen_idle_low_q;
                send_data.status.first_tick   = first_tick_q;
                send_data.status.interval_set = interval_set_q;
            end
            // Read back the number of elapsed cycles
            CONTROL_COMMAND_CYCLES: begin
                send_valid = 1'b1;
                send_data  = cycle_q;
            end
            // Set/clear the interval (number of cycles to run for)
            CONTROL_COMMAND_INTERVAL: begin
                interval       = ib_fifo_data.raw.payload;
                interval_count = 'd0;
                interval_set   = (ib_fifo_data.raw.payload != 0);
            end
            // Soft reset request
            CONTROL_COMMAND_RESET: begin
                soft_reset = ib_fifo_data.raw.payload[0];
            end
            // Catch-all
            default: begin
                send_valid = 1'b0;
            end
        endcase
        // Pop the FIFO
        ib_fifo_pop = 1'b1;
    end
end

// =============================================================================
// Trigger Generation
// =============================================================================

// Create a summary of column idle state
assign all_idle = &i_mesh_idle;

// Monitor for idle going low after each trigger event
assign seen_idle_low = (|trigger) ? 1'b0 : (seen_idle_low_q || !all_idle_q);

// Generate column triggers
assign trigger = {COLUMNS{active_q && seen_idle_low_q && all_idle_q}};

// Track the first trigger into the mesh
assign first_tick = first_tick_q && (trigger == 'd0);

// Drive mesh trigger
assign o_mesh_trigger = trigger_q;

// =============================================================================
// Cycle Counter
// =============================================================================

assign cycle = (|trigger) ? (cycle_q + { {(TX_PYLD_WIDTH-1){1'b0}}, 1'b1 }) : cycle_q;

// =============================================================================
// Debug Status Flags
// =============================================================================

assign o_status_active  = active_q;
assign o_status_idle    = all_idle_q;
assign o_status_trigger = |trigger_q;

endmodule : nx_control
