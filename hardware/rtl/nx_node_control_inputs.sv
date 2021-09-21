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

// nx_node_control_inputs
// Handle input signal state updates
//
module nx_node_control_inputs
import NXConstants::*;
#(
    parameter INPUTS = 8
) (
      input logic                  clk_i
    , input logic                  rst_i
    // External trigger signal
    , input  logic                 trigger_i
    // Signal state update
    , input  logic [IOR_WIDTH-1:0] signal_index_i
    , input  logic                 signal_is_seq_i
    , input  logic                 signal_state_i
    , input  logic                 signal_valid_i
    // Loopback interface
    , input  logic [IOR_WIDTH-1:0] loopback_index_i
    , input  logic                 loopback_state_i
    , input  logic                 loopback_valid_i
    // Interface to core
    , output logic                 core_trigger_o
    , output logic [INPUTS-1:0]    core_inputs_o
);

// =============================================================================
// Internal signals & state
// =============================================================================

// First cycle marker
`DECLARE_DQ(1, first_cycle, clk_i, rst_i, 'd1)

// Current and next cycle accumulated inputs
`DECLARE_DQ(INPUTS, input_curr, clk_i, rst_i, 'd0)
`DECLARE_DQ(INPUTS, input_next, clk_i, rst_i, 'd0)

// Core trigger signal
`DECLARE_DQ(1, input_trigger, clk_i, rst_i, 'd0)

// =============================================================================
// Drive outputs
// =============================================================================

assign core_trigger_o = input_trigger_q;
assign core_inputs_o  = input_curr_q;

// =============================================================================
// Handle input updates
// =============================================================================

always_comb begin : p_input_update
    int i;
    `INIT_D(first_cycle);
    `INIT_D(input_curr);
    `INIT_D(input_next);

    // Clear the trigger by default
    input_trigger = 1'b0;

    // If the external trigger is raised...
    if (trigger_i) begin
        // Copy next state into current, and look for differences
        for (i = 0; i < INPUTS; i++) begin
            // If there is a difference in input, trigger execution
            if (input_curr[i] != input_next[i]) input_trigger = 1'b1;
            // Keep track of the state
            input_curr[i] = input_next[i];
        end
        // On the very first cycle after setup, always trigger
        input_trigger = input_trigger || first_cycle;
        first_cycle   = 1'b0;
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
            input_trigger = (
                input_trigger || (input_curr_q[signal_index_i] != signal_state_i)
            );
        end
    end

    // Output->input loopbacks - only ever sequential (avoid deadlock loop)
    if (loopback_valid_i) input_next[loopback_index_i] = loopback_state_i;
end


endmodule : nx_node_control_inputs
