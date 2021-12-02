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
`DECLARE_DQ(            1, soft_reset,     i_clk, i_rst, 'd0)
`DECLARE_DQ(            1, seen_idle_low,  i_clk, i_rst, 'd0)
`DECLARE_DQ(RX_PYLD_WIDTH, interval,       i_clk, i_rst, 'd0)
`DECLARE_DQ(RX_PYLD_WIDTH, interval_count, i_clk, i_rst, 'd0)
`DECLARE_DQ(            1, interval_set,   i_clk, i_rst, 'd0)
`DECLARE_DQ(TX_PYLD_WIDTH, send_data,      i_clk, i_rst, 'd0)
`DECLARE_DQ(            1, send_valid,     i_clk, i_rst, 'd0)
`DECLARE_DQ(            1, all_idle,       i_clk, i_rst, 'd0)

// Trigger generation
`DECLARE_DQ(      1, active,       i_clk, i_rst, 'd0)
`DECLARE_DQ(      1, first_tick,   i_clk, i_rst, 'd1)
`DECLARE_DQ(COLUMNS, trigger,      i_clk, i_rst, 'd0)
`DECLARE_DQ(COLUMNS, trigger_mask, i_clk, i_rst, {COLUMNS{1'b1}})

// Cycle counter
`DECLARE_DQ(TX_PYLD_WIDTH, cycle, i_clk, i_rst, 'd0)

// Inbound FIFO
control_message_t ib_fifo_data;
logic             ib_fifo_empty, ib_fifo_full, ib_fifo_push;

// Message decoding
logic                     msg_stall, msg_next;
logic                     is_cmd_param, is_cmd_active, is_cmd_status,
                          is_cmd_cycles, is_cmd_interval, is_cmd_reset,
                          is_cmd_trigmask;
control_param_t           req_param;
logic [TX_PYLD_WIDTH-1:0] resp_param, resp_cycles;
control_status_t          resp_status;

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
    , .i_rd_pop  ( msg_next       )
    // Status
    , .o_level   (                )
    , .o_empty   ( ib_fifo_empty  )
    , .o_full    ( ib_fifo_full   )
);

// =============================================================================
// Message Handling
// =============================================================================

// Detect a stall
assign msg_stall = o_outbound_valid && !i_outbound_ready;
assign msg_next  = !msg_stall && !ib_fifo_empty;

// Detect each message type
assign is_cmd_param    = msg_next && (ib_fifo_data.raw.command == CONTROL_COMMAND_PARAM   );
assign is_cmd_active   = msg_next && (ib_fifo_data.raw.command == CONTROL_COMMAND_ACTIVE  );
assign is_cmd_status   = msg_next && (ib_fifo_data.raw.command == CONTROL_COMMAND_STATUS  );
assign is_cmd_cycles   = msg_next && (ib_fifo_data.raw.command == CONTROL_COMMAND_CYCLES  );
assign is_cmd_interval = msg_next && (ib_fifo_data.raw.command == CONTROL_COMMAND_INTERVAL);
assign is_cmd_reset    = msg_next && (ib_fifo_data.raw.command == CONTROL_COMMAND_RESET   );
assign is_cmd_trigmask = msg_next && (ib_fifo_data.raw.command == CONTROL_COMMAND_TRIGMASK);

// Handle interval updates
assign interval     = is_cmd_interval ? ib_fifo_data.raw.payload : interval_q;
assign interval_set = is_cmd_interval ? (ib_fifo_data.raw.payload != 'd0) : interval_set_q;

// Handle active
assign active = (
    is_cmd_active
        ? ib_fifo_data.active.active
        : ((interval_set_q && interval_count_q == interval_q) ? 'd0 : active_q)
);

// Handle interval counting
assign interval_count = (
    (is_cmd_interval || (interval_set_q && interval_count_q == interval_q))
        ? 'd0
        : interval_count_q + ((|trigger_q) ? 'd1 : 'd0)
);

// Handle soft reset
assign soft_reset = is_cmd_reset ? ib_fifo_data.raw.payload[0] : soft_reset_q;

// Handle trigger mask
assign trigger_mask = is_cmd_trigmask ? ib_fifo_data.raw.payload[COLUMNS-1:0] : trigger_mask_q;

// Build parameter response
assign req_param  = ib_fifo_data.param.param;
assign resp_param = (
    (req_param == CONTROL_PARAM_ID            ) ? { {(MESSAGE_WIDTH-24){1'b0}}, HW_DEV_ID[23:0] } :
    (req_param == CONTROL_PARAM_VERSION       ) ? { {(MESSAGE_WIDTH-16){1'b0}}, HW_VER_MAJOR[7:0], HW_VER_MINOR[7:0] } :
    (req_param == CONTROL_PARAM_COUNTER_WIDTH ) ? TX_PYLD_WIDTH[TX_PYLD_WIDTH-1:0] :
    (req_param == CONTROL_PARAM_ROWS          ) ? ROWS[TX_PYLD_WIDTH-1:0] :
    (req_param == CONTROL_PARAM_COLUMNS       ) ? COLUMNS[TX_PYLD_WIDTH-1:0] :
    (req_param == CONTROL_PARAM_NODE_INPUTS   ) ? INPUTS[TX_PYLD_WIDTH-1:0] :
    (req_param == CONTROL_PARAM_NODE_OUTPUTS  ) ? OUTPUTS[TX_PYLD_WIDTH-1:0] :
    (req_param == CONTROL_PARAM_NODE_REGISTERS) ? REGISTERS[TX_PYLD_WIDTH-1:0]
                                                : 'd0
);

// Build status response
assign resp_status.active       = active_q;
assign resp_status.idle_low     = seen_idle_low_q;
assign resp_status.first_tick   = first_tick_q;
assign resp_status.interval_set = interval_set_q;
assign resp_status._padding_0   = 'd0;

// Build cycle response
assign resp_cycles = cycle_q;

// Select the correct response
assign send_data = (
    msg_stall ? send_data_q
              : (is_cmd_param  ? resp_param  :
                 is_cmd_status ? resp_status :
                 is_cmd_cycles ? resp_cycles
                               : 'd0)
);
assign send_valid = (is_cmd_param || is_cmd_status || is_cmd_cycles || msg_stall);

// Drive outputs with send data
assign o_outbound_data  = send_data_q;
assign o_outbound_valid = send_valid_q;

// =============================================================================
// Trigger Generation
// =============================================================================

// Create a summary of column idle state
assign all_idle = &i_mesh_idle;

// Monitor for idle going low after each trigger event
assign seen_idle_low = (|trigger) ? 1'b0 : (seen_idle_low_q || !all_idle_q);

// Generate column triggers
assign trigger = {COLUMNS{active_q && seen_idle_low_q && all_idle_q}} & trigger_mask_q;

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
