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

// nx_node_control
// Handles I/O mappings, signal state updates, and generates messages for output
// signal state updates.
//
module nx_node_control #(
      parameter ADDR_ROW_WIDTH  =   4 // Row address bit width
    , parameter ADDR_COL_WIDTH  =   4 // Column address bit width
    , parameter INPUTS          =   8 // Number of inputs to each node
    , parameter OUTPUTS         =   8 // Number of outputs from each node
    , parameter OP_STORE_LENGTH = 512 // Total number of output messages allowed
    , parameter OP_STORE_WIDTH  = 1 + ADDR_ROW_WIDTH + ADDR_COL_WIDTH + $clog2(INPUTS) + 1
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
    , output nx_message_t   msg_data_o
    , output nx_direction_t msg_dir_o
    , output logic          msg_valid_o
    , input  logic          msg_ready_i
    // I/O mapping
    , input  logic [$clog2(OUTPUTS)-1:0] map_idx_i     // Which output to configure
    , input  logic [ ADDR_ROW_WIDTH-1:0] map_tgt_row_i // Target node's row
    , input  logic [ ADDR_COL_WIDTH-1:0] map_tgt_col_i // Target node's column
    , input  logic [ $clog2(INPUTS)-1:0] map_tgt_idx_i // Target node's input index
    , input  logic                       map_tgt_seq_i // Target node's input is sequential
    , input  logic                       map_valid_i   // Mapping is valid
    // Signal state update
    , input  logic [$clog2(OUTPUTS)-1:0] signal_index_i  // Input index
    , input  logic                       signal_is_seq_i // Input is sequential
    , input  logic                       signal_state_i  // Signal state
    , input  logic                       signal_valid_i  // Update is valid
    // Interface to core
    , output logic               core_trigger_o // Start/restart instruction execution
    , output logic [ INPUTS-1:0] core_inputs_o  // Collected input state
    , input  logic [OUTPUTS-1:0] core_outputs_i // Output state from core
    // Interface to memory
    , output logic [$clog2(OP_STORE_LENGTH)-1:0] store_addr_o    // Output store row address
    , output logic [         OP_STORE_WIDTH-1:0] store_wr_data_o // Output store write data
    , output logic                               store_wr_en_o   // Output store write enable
    , output logic                               store_rd_en_o   // Output store read enable
    , input  logic [         OP_STORE_WIDTH-1:0] store_rd_data_i // Output store read data
);

// Parameters and constants
localparam OP_STORE_ADDR_W = $clog2(OP_STORE_LENGTH);
localparam INPUT_W         = $clog2(INPUTS);
localparam OUTPUT_W        = $clog2(OUTPUTS);

// Internal state
`DECLARE_DQ(1, first_cycle, clk_i, rst_i, 1'b1)

`DECLARE_DQT(nx_msg_sig_state_t, msg_data,     clk_i, rst_i, {$bits(nx_msg_sig_state_t){1'b0}})
`DECLARE_DQT(nx_direction_t,     msg_dir,      clk_i, rst_i, NX_DIRX_NORTH)
`DECLARE_DQ(1,                   msg_valid,    clk_i, rst_i, 1'b0)

`DECLARE_DQ(INPUTS, input_curr, clk_i, rst_i, {INPUTS{1'b0}})
`DECLARE_DQ(INPUTS, input_next, clk_i, rst_i, {INPUTS{1'b0}})
`DECLARE_DQ(1,      input_trig, clk_i, rst_i, 1'b0)

`DECLARE_DQ(      OUTPUTS,                  output_actv,  clk_i, rst_i, {OUTPUTS{1'b0}})
`DECLARE_DQ_ARRAY(OP_STORE_ADDR_W, OUTPUTS, output_base,  clk_i, rst_i, {OP_STORE_ADDR_W{1'b0}})
`DECLARE_DQ_ARRAY(OP_STORE_ADDR_W, OUTPUTS, output_final, clk_i, rst_i, {OP_STORE_ADDR_W{1'b0}})
`DECLARE_DQ(      OP_STORE_ADDR_W,          output_next,  clk_i, rst_i, {OP_STORE_ADDR_W{1'b0}})

`DECLARE_DQ(INPUT_W, loopback_index, clk_i, rst_i, {INPUT_W{1'b0}})
`DECLARE_DQ(1,       loopback_state, clk_i, rst_i, 1'b0)
`DECLARE_DQ(1,       loopback_valid, clk_i, rst_i, 1'b0)

`DECLARE_DQ(1, fifo_pop, clk_i, rst_i, 1'b0)

// Construct outputs
assign msg_data_o  = msg_data_q;
assign msg_dir_o   = msg_dir_q;
assign msg_valid_o = msg_valid_q;

assign core_trigger_o = input_trig_q;
assign core_inputs_o  = input_curr_q;

// Detect change in output vector
`DECLARE_DQ(OUTPUTS, detect_last, clk_i, rst_i, {OUTPUTS{1'b0}})
`DECLARE_DQ(OUTPUTS, detect_xor,  clk_i, rst_i, {OUTPUTS{1'b0}})

`DECLARE_DQ(OUTPUT_W, detect_index, clk_i, rst_i, {OUTPUT_W{1'b0}})
`DECLARE_DQ(       1, detect_state, clk_i, rst_i, 1'b0)
`DECLARE_DQ(       1, detect_valid, clk_i, rst_i, 1'b0)

`DECLARE_DQ(OP_STORE_ADDR_W, update_base,  clk_i, rst_i, {OP_STORE_ADDR_W{1'b0}})
`DECLARE_DQ(OP_STORE_ADDR_W, update_final, clk_i, rst_i, {OP_STORE_ADDR_W{1'b0}})
`DECLARE_DQ(              1, update_state, clk_i, rst_i, 1'b0)
`DECLARE_DQ(              1, update_valid, clk_i, rst_i, 1'b0)

always_comb begin : p_detect_xor
    int i;

    `INIT_D(detect_last);
    `INIT_D(detect_xor);

    `INIT_D(detect_index);
    `INIT_D(detect_state);
    `INIT_D(detect_valid);

    `INIT_D(update_base);
    `INIT_D(update_final);
    `INIT_D(update_state);
    `INIT_D(update_valid);

    // If update FIFO not full, clear update valid
    if (!queue_full) update_valid = 1'b0;

    // Pipelined address lookup
    if (!update_valid) begin
        update_base  = output_base_q[detect_index_q];
        update_final = output_final_q[detect_index_q];
        update_state = detect_state;
        update_valid = detect_valid;
        detect_valid = 1'b0;
    end

    // Pipelined priority encoder to find first changed output
    for (i = 0; i < OUTPUTS; i = (i + 1)) begin
        if (!detect_valid && detect_xor[i]) begin
            detect_index  = i[OUTPUT_W-1:0];
            detect_state  = detect_last[i];
            detect_valid  = 1'b1;
            detect_xor[i] = 1'b0;
        end
    end

    // If detect_xor cleared, take the next snapshot
    if (!(|detect_xor)) begin
        detect_xor  = core_outputs_i ^ detect_last;
        detect_last = core_outputs_i;
    end
end

// Update request queue
logic [OP_STORE_ADDR_W-1:0] queued_base, queued_final;
logic                       queued_state, queue_full, queue_empty, queue_pop;

nx_fifo #(
      .DEPTH(2)
    , .WIDTH(OP_STORE_ADDR_W + OP_STORE_ADDR_W + 1)
) queue_fifo (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Write interface
    , .wr_data_i({ update_base, update_final, update_state })
    , .wr_push_i(update_valid && !queue_full)
    // Read interface
    , .rd_data_o({ queued_base, queued_final, queued_state })
    , .rd_pop_i (queue_pop)
    // Status
    , .level_o(           )
    , .empty_o(queue_empty)
    , .full_o (queue_full )
);

// Handle output message memory interface
`DECLARE_DQ(OP_STORE_ADDR_W, store_addr,    clk_i, rst_i, {OP_STORE_ADDR_W{1'b0}})
`DECLARE_DQ(OP_STORE_WIDTH,  store_wr_data, clk_i, rst_i, {OP_STORE_WIDTH{1'b0}})
`DECLARE_DQ(1,               store_wr_en,   clk_i, rst_i, 1'b0)
`DECLARE_DQ(1,               store_rd_en,   clk_i, rst_i, 1'b0)
`DECLARE_DQ(1,               store_rd_resp, clk_i, rst_i, 1'b0)

`DECLARE_DQ(OP_STORE_ADDR_W, send_address, clk_i, rst_i, {OP_STORE_ADDR_W{1'b0}})
`DECLARE_DQ(OP_STORE_ADDR_W, send_final,   clk_i, rst_i, {OP_STORE_ADDR_W{1'b0}})
`DECLARE_DQ(1,               send_pending, clk_i, rst_i, 1'b0)
`DECLARE_DQ(1,               send_value,   clk_i, rst_i, 1'b0)

assign store_addr_o    = store_addr_q;
assign store_wr_data_o = store_wr_data_q;
assign store_wr_en_o   = store_wr_en_q;
assign store_rd_en_o   = store_rd_en_q;

logic state_fifo_out, state_fifo_full, state_fifo_empty;

nx_fifo #(
      .DEPTH   (3)
    , .WIDTH   (1)
    , .FULL_LVL(2)
) output_state_fifo (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Write interface
    , .wr_data_i(send_value )
    , .wr_push_i(store_rd_en)
    // Read interface
    , .rd_data_o(state_fifo_out)
    , .rd_pop_i (fifo_pop      )
    // Status
    , .level_o(                )
    , .empty_o(state_fifo_empty)
    , .full_o (state_fifo_full )
);

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
    `INIT_D(send_address);
    `INIT_D(send_final);
    `INIT_D(send_pending);
    `INIT_D(send_value);

    // Pipeline store_rd_en -> store_rd_resp to align with data return
    store_rd_resp = store_rd_en;

    // Always clear write and read enable
    store_wr_en = 1'b0;
    store_rd_en = 1'b0;

    // Always clear queue pop
    queue_pop = 1'b0;

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

    // Otherwise handle output state generation
    end else if (!state_fifo_full) begin
        // Increment to the next address to fetch
        if (send_pending) begin
            store_addr   = send_address;
            send_address = send_address + { {(OP_STORE_ADDR_W-1){1'b0}}, 1'b1 };
            store_rd_en  = 1'b1;

        // Pick-up the next update request
        end else if (!queue_empty) begin
            store_addr   = queued_base;
            send_address = queued_base + { {(OP_STORE_ADDR_W-1){1'b0}}, 1'b1 };
            send_final   = queued_final;
            send_value   = queued_state;
            store_rd_en  = 1'b1;
            queue_pop    = 1'b1;

        end

        // Check for further messages to send
        send_pending = store_rd_en && (store_addr != send_final);

    end
end

// Token acquisition
`DECLARE_DQ(1, token_held,    clk_i, rst_i, 1'b0)
`DECLARE_DQ(1, token_release, clk_i, rst_i, 1'b0)

assign token_release_o = token_release_q;

always_comb begin : p_token
    `INIT_D(token_held);
    `INIT_D(token_release);

    // If token released, clear it
    if (token_release) token_held = 1'b0;

    // Always clear token release
    token_release = 1'b0;

    // If holding token and nothing more to do, release it
    if (token_held && state_fifo_empty && !msg_valid_o) begin
        token_release = 1'b1;

    // If not holding token and one presented
    end else if (!token_held && token_grant_i) begin
        token_held    = !state_fifo_empty;
        token_release =  state_fifo_empty;

    end
end

// Generate output messages
logic [OP_STORE_WIDTH-1:0] msg_fifo_out;
logic                      msg_fifo_empty;

nx_fifo #(
      .DEPTH(             3)
    , .WIDTH(OP_STORE_WIDTH)
) output_msg_fifo (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Write interface
    , .wr_data_i(store_rd_data_i)
    , .wr_push_i(store_rd_resp_q)
    // Read interface
    , .rd_data_o(msg_fifo_out)
    , .rd_pop_i (fifo_pop    )
    // Status
    , .level_o(              )
    , .empty_o(msg_fifo_empty)
    , .full_o (              )
);

assign idle_o = (
    queue_empty && state_fifo_empty && msg_fifo_empty && !msg_valid_q &&
    !loopback_valid_q && !(|detect_xor) && !detect_valid && !store_rd_en &&
    !input_trig_q && !update_valid
);

always_comb begin : p_output
    logic                      tgt_lb;
    logic [ADDR_ROW_WIDTH-1:0] tgt_row;
    logic [ADDR_COL_WIDTH-1:0] tgt_col;
    logic [       INPUT_W-1:0] tgt_idx;
    logic                      tgt_seq;

    `INIT_D(msg_data);
    `INIT_D(msg_dir);
    `INIT_D(msg_valid);
    `INIT_D(loopback_index);
    `INIT_D(loopback_state);
    `INIT_D(loopback_valid);
    `INIT_D(fifo_pop);

    // Clear message valid if accepted
    if (msg_ready_i) msg_valid = 1'b0;

    // Decode the fields from the RAM
    { tgt_lb, tgt_row, tgt_col, tgt_idx, tgt_seq } = msg_fifo_out;

    // Handle internal updates
    loopback_index = tgt_idx;
    loopback_state = state_fifo_out;
    loopback_valid = (
        !state_fifo_empty && // Entries ready in state FIFO
        !msg_fifo_empty   && // Entries ready in message FIFO
        tgt_lb               // Loopback flag set (calculated when filling RAM)
    );

    // Pop FIFO if loopback used
    fifo_pop = loopback_valid;

    // Generate the next message
    if (!msg_valid && !tgt_lb && token_held_q) begin
        // Build the message to send
        msg_data.header.row     = tgt_row;
        msg_data.header.column  = tgt_col;
        msg_data.header.command = NX_CMD_SIG_STATE;
        msg_data.target_index   = tgt_idx;
        msg_data.target_is_seq  = tgt_seq;
        msg_data.state          = state_fifo_out;

        // Route the message
        if      (tgt_row < node_row_i) msg_dir = NX_DIRX_NORTH;
        else if (tgt_row > node_row_i) msg_dir = NX_DIRX_SOUTH;
        else if (tgt_col < node_col_i) msg_dir = NX_DIRX_WEST;
        else if (tgt_col > node_col_i) msg_dir = NX_DIRX_EAST;

        // Send when both state and message and not an internal loopback
        msg_valid = !state_fifo_empty && !msg_fifo_empty;

        // Pop FIFO if message queued up
        fifo_pop = msg_valid;
    end
end

// Handle input updates
always_comb begin : p_input_update
    int i;
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
    if (signal_valid_i) begin
        // Always update the next state
        input_next[signal_index_i] = signal_state_i;
        // If not sequential...
        if (!signal_is_seq_i) begin
            // Update the current signal state
            input_curr[signal_index_i] = signal_state_i;
            // Determine if re-triggering is necessary
            input_trig = input_trig || (input_curr_q[signal_index_i] != signal_state_i);
        end
    end

    // Output->input loopbacks - only ever sequential (avoid deadlock loop)
    if (loopback_valid_q) input_next[loopback_index_q] = loopback_state_q;
end

endmodule : nx_node_control
