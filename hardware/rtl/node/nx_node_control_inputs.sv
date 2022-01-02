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
// Handles input state updates and output loopbacks, and generates the trigger
// signal for the logic core.
//
module nx_node_control_inputs
import NXConstants::*;
#(
      parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter EXT_INPUTS =  0
) (
      input  logic                      i_clk
    , input  logic                      i_rst
    // Control signals
    , input  logic                      i_trigger
    , output logic                      o_idle
    // Inputs from decoder
    , input  logic [INPUTS-1:0]         i_loopback_mask
    , input  logic [$clog2(INPUTS)-1:0] i_input_index
    , input  logic                      i_input_value
    , input  logic                      i_input_is_seq
    , input  logic                      i_input_update
    // Interface to logic core
    , output logic [INPUTS-1:0]         o_core_inputs
    , input  logic [OUTPUTS-1:0]        i_core_outputs
    , output logic                      o_core_trigger
    // External inputs
    , input  logic                      i_ext_inputs_en
    , input  logic [INPUTS-1:0]         i_ext_inputs
);

// =============================================================================
// Constants
// =============================================================================

localparam INPUT_WIDTH = $clog2(INPUTS);

// =============================================================================
// Internal Signals and State
// =============================================================================

// Flops
`DECLARE_DQ(INPUTS, inputs_curr,  i_clk, i_rst, 'd0)
`DECLARE_DQ(INPUTS, inputs_next,  i_clk, i_rst, 'd0)
`DECLARE_DQ(     1, core_trigger, i_clk, i_rst, 'd0)

// Connect outputs
assign o_idle         = !core_trigger_q && !i_input_update && !i_trigger;
assign o_core_inputs  = inputs_curr_q;
assign o_core_trigger = core_trigger_q;

// =============================================================================
// Handle Current Cycle Inputs
// =============================================================================

// Intended behaviour:
//  - On global trigger pulse do one of two things:
//     1. If marked as a loopback, pickup the core's output value
//     2. Otherwise, take it from the 'next' input flops
//  - On a non-sequential input update from the decoder, adopt the new value
//  - Otherwise persist the current value

generate
for (genvar idx = 0; idx < INPUTS; idx++) begin : gen_current
    // Detect a non-sequential input update
    logic dcd_match;
    assign dcd_match = i_input_update && !i_input_is_seq && (i_input_index == idx[INPUT_WIDTH-1:0]);
    // Mux to select the correct input value
    assign inputs_curr[idx] = (
        i_trigger ? (i_loopback_mask[idx] ? i_core_outputs[idx] : inputs_next_q[idx])
                  : (dcd_match            ? i_input_value       : inputs_curr_q[idx])
    );
end
endgenerate

// =============================================================================
// Handle Next Cycle Inputs
// =============================================================================

generate
for (genvar idx = 0; idx < INPUTS; idx++) begin : gen_next
    // Detect any input update (sequential or non-sequential)
    logic dcd_match;
    assign dcd_match = i_input_update && (i_input_index == idx[INPUT_WIDTH-1:0]);
    // If external inputs are configured and enabled, always take that value
    if (EXT_INPUTS) begin
        assign inputs_next[idx] = i_ext_inputs_en ? i_ext_inputs[idx] :
                                  dcd_match       ? i_input_value
                                                  : inputs_next_q[idx];
    // Otherwise pickup new value from an incoming message
    end else begin
        assign inputs_next[idx] = (dcd_match ? i_input_value : inputs_next_q[idx]);
    end
end
endgenerate

// =============================================================================
// Generate Core Trigger Pulse
// =============================================================================

// Whenever global trigger is presented, or current cycle inputs have changed
assign core_trigger = i_trigger || (inputs_curr != inputs_curr_q);

// =============================================================================
// Unused Tie-Offs
// =============================================================================

generate
if (!EXT_INPUTS) begin
    logic _unused;
    assign _unused = &{ 1'b0, i_ext_inputs_en, i_ext_inputs };
end
endgenerate

endmodule : nx_node_control_inputs
