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

// nx_node_core
// Evaluates instruction sequence against input values and internal register
// state to produce outputs
//
module nx_node_core
import NXConstants::*;
#(
      parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter REGISTERS  = 16
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic                        i_clk
    , input  logic                        i_rst
    // I/O from simulated logic
    , input  logic [ INPUTS-1:0]          i_inputs
    , output logic [OUTPUTS-1:0]          o_outputs
    // Execution controls
    , input  logic [NODE_PARAM_WIDTH-1:0] i_populated
    , input  logic                        i_trigger
    , output logic                        o_idle
    // Instruction fetch
    , output logic [RAM_ADDR_W-1:0]       o_instr_addr
    , output logic                        o_instr_rd_en
    , input  logic [RAM_DATA_W-1:0]       i_instr_rd_data
    , input  logic                        i_instr_stall
);

// =============================================================================
// Constants
// =============================================================================

localparam OUTPUT_IDX_W = $clog2(OUTPUTS);
localparam REG_IDX_W    = $clog2(REGISTERS);

typedef enum logic { IDLE, ACTIVE } state_t;

// =============================================================================
// Internal signals and state
// =============================================================================

// Pipeline state
`DECLARE_DQT(state_t, fetch_state,  i_clk, i_rst, IDLE)
`DECLARE_DQT(state_t, exec_state,   i_clk, i_rst, IDLE)

// Fetch state
`DECLARE_DQ(RAM_ADDR_W, pc,           i_clk, i_rst, 'd0)
`DECLARE_DQ(1,          held_trigger, i_clk, i_rst, 'd0)

logic start_fetch;

// Execute state
instruction_t decoded;
logic         exec_active, exec_output, result;
logic [2:0]   table_index;

`DECLARE_DQ(REGISTERS,     working,     i_clk, i_rst, {REGISTERS{1'b0}})
`DECLARE_DQ(OUTPUTS,       outputs,     i_clk, i_rst, {OUTPUTS{1'b0}})
`DECLARE_DQ(MAX_IOR_WIDTH, output_idx,  i_clk, i_rst, {OUTPUT_IDX_W{1'b0}})

// =============================================================================
// Determine idleness
// =============================================================================

assign o_idle = (fetch_state_q == IDLE) && (exec_state_q == IDLE) && !held_trigger_q;

// =============================================================================
// Fetch handling
// =============================================================================

// Postpone a trigger arriving during active execution
assign held_trigger = (i_trigger || held_trigger_q) && (fetch_state_q == ACTIVE);

// Start fetch from IDLE if a trigger is presented (or one was postponed)
assign start_fetch = (fetch_state_q == IDLE) && (held_trigger_q || i_trigger);

// Track fetch state
assign fetch_state = (start_fetch || fetch_state_q) && (pc_q != i_populated[RAM_ADDR_W-1:0]);

// Increment PC when active and not stalled
assign pc = fetch_state ? (i_instr_stall ? pc_q : (pc_q + 'd1)) : 'd0;

// Drive outputs
assign o_instr_addr  = pc_q;
assign o_instr_rd_en = (fetch_state == ACTIVE);

// =============================================================================
// Execution
// =============================================================================

// Pipeline state from fetch
assign exec_state = fetch_state_q;

// Determine if execute is active
assign exec_active = (exec_state == ACTIVE) && !i_instr_stall;

// Decode the instruction
assign decoded = i_instr_rd_data[$bits(instruction_t)-1:0];

// Mux the correct input values
assign table_index = {
    (decoded.src_a_ip ? i_inputs[decoded.src_a] : working_q[decoded.src_a[REG_IDX_W-1:0]]),
    (decoded.src_b_ip ? i_inputs[decoded.src_b] : working_q[decoded.src_b[REG_IDX_W-1:0]]),
    (decoded.src_c_ip ? i_inputs[decoded.src_c] : working_q[decoded.src_c[REG_IDX_W-1:0]])
};

// Lookup result in the truth table
assign result = (decoded.truth >> table_index) & 1'b1;

// Update the working registers
generate
for (genvar idx = 0; idx < REGISTERS; idx++) begin : gen_working_reg
    assign working[idx] = (
        (exec_active && decoded.tgt_reg[REG_IDX_W-1:0] == idx)
            ? result : working_q[idx]
    );
end
endgenerate

// Determine if an output should be generated
assign exec_output = exec_active && decoded.gen_out;

// Update the output vector if required
generate
for (genvar idx = 0; idx < OUTPUTS; idx++) begin : gen_output
    assign outputs[idx] = (
        (exec_output && output_idx_q == idx) ? result : outputs_q[idx]
    );
end
endgenerate

// Increment the output index whenever an output is generated, reset to zero
// when execution goes idle
assign output_idx = exec_output          ? (output_idx_q + 'd1) : (
                    (exec_state == IDLE) ? 'd0
                                         : output_idx_q);

// Drive outputs
assign o_outputs = outputs_q;

endmodule : nx_node_core
