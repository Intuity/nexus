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
module nx_node_control #(
      parameter STREAM_WIDTH   = 32
    , parameter ADDR_ROW_WIDTH = 4
    , parameter ADDR_COL_WIDTH = 4
    , parameter COMMAND_WIDTH  =  2
    , parameter INPUTS         =  8
    , parameter OUTPUTS        =  8
    , parameter MAX_IO         = ((INPUTS > OUTPUTS) ? INPUTS : OUTPUTS)
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
    , output logic [STREAM_WIDTH-1:0] msg_data_o
    , output logic [             1:0] msg_dir_o
    , output logic                    msg_valid_o
    , input  logic                    msg_ready_i
    // I/O mapping
    , input  logic [ $clog2(MAX_IO)-1:0] map_io_i         // Which slot to configure
    , input  logic                       map_input_i      // High - maps an input, low - maps an output
    , input  logic [ ADDR_ROW_WIDTH-1:0] map_remote_row_i // The destination/source node row
    , input  logic [ ADDR_COL_WIDTH-1:0] map_remote_col_i // The destination/source node column
    , input  logic [$clog2(OUTPUTS)-1:0] map_remote_idx_i // The destination/source node I/O index
    , input  logic                       map_slot_i       // Which slot to program (for multiple outputs)
    , input  logic                       map_broadcast_i  // Flag to send output as broadcast
    , input  logic                       map_seq_i        // Flag to set input as sequential
    , input  logic                       map_valid_i      // Mapping is valid
    // Signal state update
    , input  logic [ ADDR_ROW_WIDTH-1:0] signal_remote_row_i // The source node row
    , input  logic [ ADDR_COL_WIDTH-1:0] signal_remote_col_i // The source node column
    , input  logic [$clog2(OUTPUTS)-1:0] signal_remote_idx_i // The source node output index
    , input  logic                       signal_state_i      // State of the signal
    , input  logic                       signal_valid_i      // Signal update is valid
    // Interface to core
    , output logic               core_trigger_o // Start/restart instruction execution
    , output logic [ INPUTS-1:0] core_inputs_o  // Collected input state
    , input  logic [OUTPUTS-1:0] core_outputs_i // Output state from core
);

// Parameters and constants
localparam BIT_INDEX_WIDTH = $clog2(MAX_IO);
localparam BC_DECAY_WIDTH  = ADDR_ROW_WIDTH + ADDR_COL_WIDTH;
localparam IN_KEY_WIDTH    = ADDR_ROW_WIDTH + ADDR_COL_WIDTH + BIT_INDEX_WIDTH;
localparam OUT_KEY_WIDTH   = 1 + ADDR_ROW_WIDTH + ADDR_COL_WIDTH;
localparam PAYLOAD_WIDTH   = (
    STREAM_WIDTH - 1 - ADDR_ROW_WIDTH - ADDR_COL_WIDTH - COMMAND_WIDTH
);

`include "nx_constants.svh"

typedef enum logic [1:0] {
    OUTPUT_WAIT,
    OUTPUT_SENT_A,
    OUTPUT_SENT_B
} output_state_t;

// Internal state
`DECLARE_DQ(1, first_cycle, clk_i, rst_i, 1'b1)

`DECLARE_DQ(1, token_held,    clk_i, rst_i, 1'b0)
`DECLARE_DQ(1, token_release, clk_i, rst_i, 1'b0)

`DECLARE_DQ(INPUTS, input_curr, clk_i, rst_i, {INPUTS{1'b0}})
`DECLARE_DQ(INPUTS, input_next, clk_i, rst_i, {INPUTS{1'b0}})
`DECLARE_DQ(1,      input_trig, clk_i, rst_i, 1'b0)
`DECLARE_DQ(INPUTS, input_seq,  clk_i, rst_i, {INPUTS{1'b0}})
`DECLARE_DQ(INPUTS, input_actv, clk_i, rst_i, {INPUTS{1'b0}})
`DECLARE_DQ_ARRAY(IN_KEY_WIDTH, INPUTS, input_map, clk_i, rst_i, {IN_KEY_WIDTH{1'b0}})

`DECLARE_DQ(OUTPUTS,         output_last,  clk_i, rst_i, {OUTPUTS{1'b0}})
`DECLARE_DQ($clog2(OUTPUTS), output_idx,   clk_i, rst_i, {$clog2(OUTPUTS){1'b0}})
`DECLARE_DQ(2,               output_state, clk_i, rst_i, OUTPUT_WAIT)
`DECLARE_DQ_ARRAY(OUT_KEY_WIDTH, OUTPUTS, output_map_a, clk_i, rst_i, {OUT_KEY_WIDTH{1'b0}})
`DECLARE_DQ_ARRAY(OUT_KEY_WIDTH, OUTPUTS, output_map_b, clk_i, rst_i, {OUT_KEY_WIDTH{1'b0}})

`DECLARE_DQ(STREAM_WIDTH, msg_data,     clk_i, rst_i, {STREAM_WIDTH{1'b0}})
`DECLARE_DQ(2,            msg_dir,      clk_i, rst_i, DIRX_NORTH)
`DECLARE_DQ(4,            msg_send_dir, clk_i, rst_i, 4'd0)
`DECLARE_DQ(1,            msg_valid,    clk_i, rst_i, 1'b0)

// Construct outputs
assign idle_o = (
    (output_state   == OUTPUT_WAIT) && // Not currently preparing messages
    (core_outputs_i == output_last) && // No outstanding output changes
    !msg_valid                      && // No active message
    !msg_send_dir                      // No pending broadcast
);

assign token_release_o = token_release_q;

assign msg_data_o  = msg_data_q;
assign msg_dir_o   = msg_dir_q;
assign msg_valid_o = msg_valid_q;

assign core_trigger_o = input_trig_q;
assign core_inputs_o  = input_curr_q;

// Handle I/O mapping updates
always_comb begin : p_io_mapping
    `INIT_D(input_seq);
    `INIT_D(input_actv);
    `INIT_D_ARRAY(input_map);
    `INIT_D_ARRAY(output_map_a);
    `INIT_D_ARRAY(output_map_b);

    // Perform a mapping update
    if (map_valid_i) begin
        // Update an input mapping
        if (map_input_i) begin
            input_map[map_io_i[$clog2(INPUTS)-1:0]] = {
                map_remote_row_i, map_remote_col_i, map_remote_idx_i
            };
            input_seq[map_io_i[$clog2(INPUTS)-1:0]]  = map_seq_i;
            input_actv[map_io_i[$clog2(INPUTS)-1:0]] = 1'b1;
        // Update an output mapping for slot B
        end else if (map_slot_i) begin
            output_map_b[map_io_i[$clog2(OUTPUTS)-1:0]] = {
                map_broadcast_i, map_remote_row_i, map_remote_col_i
            };
        // Update an output mapping for slot A
        end else begin
            output_map_a[map_io_i[$clog2(OUTPUTS)-1:0]] = {
                map_broadcast_i, map_remote_row_i, map_remote_col_i
            };
        end
    end
end

// Handle signal state updates
always_comb begin : p_signal_state
    int i;
    logic [ ADDR_ROW_WIDTH-1:0] rem_row;
    logic [ ADDR_COL_WIDTH-1:0] rem_col;
    logic [BIT_INDEX_WIDTH-1:0] rem_idx;
    `INIT_D(first_cycle);
    `INIT_D(input_curr);
    `INIT_D(input_next);
    `INIT_D(input_trig);

    // Always clear the input trigger after one cycle
    input_trig = 1'b0;

    // If the external trigger is raised...
    if (trigger_i) begin
        // Copy next state into current, and look for differences
        for (i = 0; i < INPUTS; i++) begin
            // If there is a difference in input, trigger execution
            if (input_curr[i] != input_next[i]) input_trig = 1'b1;
            // Keep track of the state
            input_curr[i] = input_next[i];
        end
        // On the very first cycle after setup, always trigger
        input_trig  = input_trig | first_cycle;
        first_cycle = 1'b0;
    end

    // Perform a signal state update
    for (i = 0; i < INPUTS; i = (i + 1)) begin
        { rem_row, rem_col, rem_idx } = input_map_q[i];
        // Is this input active?
        if (input_actv_q[i]) begin
            // Handle signal state updates from the decoder
            if (
                rem_row == signal_remote_row_i &&
                rem_col == signal_remote_col_i &&
                rem_idx == signal_remote_idx_i &&
                signal_valid_i
            ) begin
                // Always update next state
                input_next[i] = signal_state_i;
                // If not sequential, update current state as well
                if (!input_seq_q[i]) begin
                    input_trig    = input_trig | (signal_state_i != input_curr[i]);
                    input_curr[i] = signal_state_i;
                end
            // Handle output->input loopbacks
            end else if (
                rem_row == node_row_i &&
                rem_col == node_col_i
            ) begin
                // Always update next state
                input_next[i] = core_outputs_i[rem_idx];
                // If not sequential, update current state as well
                if (!input_seq_q[i]) begin
                    input_trig    = input_trig | (core_outputs_i[rem_idx] != input_curr[i]);
                    input_curr[i] = core_outputs_i[rem_idx];
                end
            end
        end
    end
end

// Generate output messages when state changes
always_comb begin : p_output_state
    int i;
    logic                      tgt_bc;
    logic [ADDR_ROW_WIDTH-1:0] tgt_row;
    logic [ADDR_COL_WIDTH-1:0] tgt_col;
    logic [ OUT_KEY_WIDTH-1:0] key;
    `INIT_D(token_held);
    `INIT_D(token_release);
    `INIT_D(output_last);
    `INIT_D(output_idx);
    `INIT_D(output_state);
    `INIT_D(msg_data);
    `INIT_D(msg_dir);
    `INIT_D(msg_send_dir);
    `INIT_D(msg_valid);

    // Always clean token release on the next cycle
    token_release = 1'b0;

    // Check if token has been granted
    if (token_grant_i) token_held = 1'b1;

    // Clear the valid if message accepted
    if (msg_ready_i) msg_valid = 1'b0;

    // Track updating state
    if (!msg_valid && token_held) begin
        case (output_state)
            // Wait for a signal state to change, then send A
            OUTPUT_WAIT: begin
                for (i = 0; i < OUTPUTS; i = (i + 1)) begin
                    if (!msg_valid && core_outputs_i[i] != output_last[i]) begin
                        output_idx = i;
                        { tgt_bc, tgt_row, tgt_col } = output_map_a_q[i];
                        msg_data = {
                            tgt_bc, tgt_row, tgt_col, CMD_SIG_STATE,
                            node_row_i, node_col_i, output_idx,
                            core_outputs_i[i], 9'd0
                        };
                        // Don't transmit messages for this node
                        msg_valid = tgt_bc || tgt_row != node_row_i || tgt_col != node_col_i;
                        // Route in the correct direction
                        if (tgt_bc) begin
                            msg_send_dir = 4'hE; // All but north remaining
                            msg_dir      = DIRX_NORTH;
                        end else if (tgt_row < node_row_i) begin
                            msg_dir = DIRX_NORTH;
                        end else if (tgt_row > node_row_i) begin
                            msg_dir = DIRX_SOUTH;
                        end else if (tgt_col < node_col_i) begin
                            msg_dir = DIRX_WEST;
                        end else if (tgt_col > node_col_i) begin
                            msg_dir = DIRX_EAST;
                        end
                        // Capture updated state
                        output_last[i] = core_outputs_i[i];
                        // Change state
                        output_state = OUTPUT_SENT_A;
                    end
                end
            end
            // Wait for message A to be accepted by all directions, then possibly send B
            OUTPUT_SENT_A: begin
                // Retransmit message in as many directions as required
                if (msg_send_dir) begin
                    for (i = 0; i < 4; i = (i + 1)) begin
                        if (!msg_valid && msg_send_dir[i]) begin
                            msg_send_dir[i] = 1'b0;
                            msg_dir         = i;
                            msg_valid       = 1'b1;
                        end
                    end
                // Send output B if required
                end else if (
                    output_map_a_q[output_idx] != output_map_b_q[output_idx]
                ) begin
                    { tgt_bc, tgt_row, tgt_col } = output_map_b_q[output_idx];
                    msg_data = {
                        tgt_bc, tgt_row, tgt_col, CMD_SIG_STATE,
                        node_row_i, node_col_i, output_idx,
                        core_outputs_i[output_idx], 9'd0
                    };
                    // Don't transmit messages for this node
                    msg_valid = tgt_bc || tgt_row != node_row_i || tgt_col != node_col_i;
                    // Route in the correct direction
                    if (tgt_bc) begin
                        msg_send_dir = 4'hE; // All but north remaining
                        msg_dir      = DIRX_NORTH;
                    end else if (tgt_row < node_row_i) begin
                        msg_dir = DIRX_NORTH;
                    end else if (tgt_row > node_row_i) begin
                        msg_dir = DIRX_SOUTH;
                    end else if (tgt_col < node_col_i) begin
                        msg_dir = DIRX_WEST;
                    end else if (tgt_col > node_col_i) begin
                        msg_dir = DIRX_EAST;
                    end
                    // Change state
                    output_state = OUTPUT_SENT_B;
                // Otherwise go back to WAIT
                end else begin
                    output_state = OUTPUT_WAIT;
                end
            end
            // Wait for message B to be accepted by all directions, then return to searching
            OUTPUT_SENT_B: begin
                // Retransmit message in as many directions as required
                if (msg_send_dir) begin
                    for (i = 0; i < 4; i = (i + 1)) begin
                        if (!msg_valid && msg_send_dir[i]) begin
                            msg_send_dir[i] = 1'b0;
                            msg_dir         = i;
                            msg_valid       = 1'b1;
                        end
                    end
                // Otherwise go back to WAIT
                end else begin
                    output_state = OUTPUT_WAIT;
                end
            end
            // Default, return to WAIT
            default: output_state = OUTPUT_WAIT;
        endcase

        // If in WAIT and a token is held, release it
        if (output_state == OUTPUT_WAIT) begin
            token_release = token_held;
            token_held    = 1'b0;
        end
    end
end

endmodule : nx_node_control
