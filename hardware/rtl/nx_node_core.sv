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

`timescale 1ns/1ps

/*
Notes:
  1. Form of instructions: { OPERATION, INPUT_A, INPUT_B, TARGET, FLAG, OUTPUT }
*/

`include "nx_common.svh"

module nx_node_core #(
      parameter OP_W   =  4 // Operand encoding width
    , parameter REG_W  = 16 // Internal register width
    , parameter IO_W   =  4 // Primary inputs/outputs width
    , parameter SLOTS  = 32 // How many instruction slots are available
    , parameter INST_W = OP_W + (3 * $clog2(REG_W)) + 1 + $clog2(IO_W) // Calculate instruction width
) (
      input  logic                     clk
    , input  logic                     rst
    // External controls
    , input  logic                     tick
    // State outputs
    , output logic                     in_setup
    , output logic                     in_wait
    , output logic                     in_run
    // Instruction load
    , input  logic [       INST_W-1:0] load_instr
    , input  logic [$clog2(SLOTS)-1:0] load_slot
    , input  logic                     load_last
    , input  logic                     load_valid
    // Input load
    , input  logic                     in_value
    , input  logic [ $clog2(IO_W)-1:0] in_index
    , input  logic                     in_valid
    // Value output
    , output logic          [IO_W-1:0] out_values
    , output logic          [IO_W-1:0] out_valids
);

localparam STEP_W = $clog2(SLOTS);

typedef enum bit [1:0] {
    STATE_SETUP, // 0: Instructions are loaded in the setup phase
    STATE_WAIT,  // 1: Waiting for trigger
    STATE_RUN    // 2: Running instruction sequence
} nx_core_state_t;

typedef enum bit [OP_W-1:0] {
    OP_INVERT,
    OP_AND,
    OP_NAND,
    OP_OR,
    OP_NOR,
    OP_XOR,
    OP_XNOR
} nx_core_op_t;

// =============================================================================
// State variables
// =============================================================================

logic [  IO_W-1:0] `DECLARE_DQ(inputs,    clk, rst, {IO_W{1'b0}}  )
nx_core_state_t    `DECLARE_DQ(state,     clk, rst, STATE_SETUP   )
logic [ REG_W-1:0] `DECLARE_DQ(registers, clk, rst, {REG_W{1'b0}} )
logic [STEP_W-1:0] `DECLARE_DQ(step,      clk, rst, {STEP_W{1'b0}})
logic [  IO_W-1:0] `DECLARE_DQ(outputs,   clk, rst, {IO_W{1'b0}}  )
logic [  IO_W-1:0] `DECLARE_DQ(updated,   clk, rst, {IO_W{1'b0}}  )

// Expose state flags
assign in_setup = (m_state_q == STATE_SETUP);
assign in_wait  = (m_state_q == STATE_WAIT );
assign in_run   = (m_state_q == STATE_RUN  );

// =============================================================================
// Instruction store
// =============================================================================

// NOTE: 1-bit wider than INST_W as it carries a VALID flag where loaded
logic [INST_W:0] m_instructions [SLOTS-1:0];

// s_load_instr
// Handle load of instructions into store
//
always_ff @(posedge clk, posedge rst) begin : s_load_instr
    integer i;
    if (rst) begin
        for (i = 0; i < SLOTS; i = (i + 1)) m_instructions[i] <= {INST_W{1'b0}};
    end else if (load_valid) begin
        m_instructions[load_slot] <= {load_instr, 1'b1};
    end
end

// =============================================================================
// Combinatorial logic
// =============================================================================

// c_load_input
// Handle update of input bits from wrapper layer
//
always_comb begin : c_load_input
    `INIT_D(inputs);
    if (in_valid) m_inputs_d[in_index] = in_value;
end

// c_execute
// Execute boolean operation instructions and produce outputs
//
always_comb begin : c_execute
    integer i;

    nx_core_op_t              operation;
    logic [$clog2(REG_W)-1:0] reg_in_a, reg_in_b, reg_out;
    logic                     gen_out;
    logic [         IO_W-1:0] out_idx;
    logic                     op_valid;
    logic                     value_a, value_b, result;

    `INIT_D(state);
    `INIT_D(registers);
    `INIT_D(step);
    `INIT_D(outputs);
    `INIT_D(updated);

    case (m_state_d)
        // SETUP: Wait for the last instruction to be loaded, then transition to
        //        to WAIT phase
        STATE_SETUP: begin
            if (load_valid && load_last) m_state_d = STATE_WAIT;
        end
        // WAIT: Wait for the 'tick' pulse which signifies the rising edge of
        //       the simulated clock
        STATE_WAIT: begin
            if (tick) begin
                // Copy inputs into registers as starting point
                for (i = 0; i < IO_W; i = (i + 1)) begin
                    m_registers_d[i] = m_inputs_q[i];
                end
                // Reset to first instruction, clear output update flags
                m_step_d    = {STEP_W{1'b0}};
                m_updated_d = {IO_W{1'b0}};
                // Move to the RUN phase
                m_state_d = STATE_RUN;
            end
        end
        // RUN: Pickup the next instruction to execute
        STATE_RUN: begin
            // Decode the operation to perform
            {
                operation, reg_in_a, reg_in_b, reg_out, gen_out, out_idx,
                op_valid
            } = m_instructions[m_step_d];
            // If operation is valid, execute it
            if (op_valid) begin
                value_a = m_registers_d[reg_in_a];
                value_b = m_registers_d[reg_in_b];
                result  = 1'b0;
                case (operation)
                    OP_INVERT: result = ~(value_a          );
                    OP_AND   : result =  (value_a & value_b);
                    OP_NAND  : result = ~(value_a & value_b);
                    OP_OR    : result =  (value_a | value_b);
                    OP_NOR   : result = ~(value_a | value_b);
                    OP_XOR   : result =  (value_a ^ value_b);
                    OP_XNOR  : result = ~(value_a ^ value_b);
                endcase
                m_registers_q[reg_out] = result;
                // If output generation is marked, store and flag
                if (gen_out) begin
                    m_outputs_d[out_idx] = result;
                    m_updated_d[out_idx] = 1'b1;
                end
            end
            // For last or invalid instructions, transition to WAIT state
            if (m_step_d == SLOTS || !op_valid) m_state_d = STATE_WAIT;
            // Otherwise, move to the next instruction
            else m_step_d = m_step_d + { {(STEP_W-1){1'b0}}, 1'b1 };
        end
    endcase
end

endmodule
