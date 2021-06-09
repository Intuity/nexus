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
module nx_node_core #(
      parameter INPUTS       =   8 // Number of input signals
    , parameter OUTPUTS      =   8 // Number of output signals
    , parameter REGISTERS    =   8 // Number of internal registers
    , parameter MAX_INSTRS   = 512 // Maximum instructions
    , parameter INSTR_WIDTH  =  36 // Width of each instruction
    , parameter OPCODE_WIDTH =   3 // Width of each opcode
) (
      input  logic                          clk_i
    , input  logic                          rst_i
    // I/O from simulated logic
    , input  logic [            INPUTS-1:0] inputs_i      // Input vector
    , output logic [           OUTPUTS-1:0] outputs_o     // Output vector
    // Execution controls
    , input  logic [$clog2(MAX_INSTRS)-1:0] populated_i   // # of populated instructions
    , input  logic                          trigger_i     // Trigger execution
    , output logic                          idle_o        // Core idle flag
    // Instruction fetch
    , output logic [$clog2(MAX_INSTRS)-1:0] instr_addr_o  // Instruction fetch address
    , output logic                          instr_rd_o    // Read enable
    , input  logic [       INSTR_WIDTH-1:0] instr_data_i  // Instruction data
    , input  logic                          instr_stall_i // Fetch stall
);

// Parameters
localparam INSTR_ADDR_W = $clog2(MAX_INSTRS);
localparam OUTPUT_IDX_W = $clog2(OUTPUTS);
localparam REG_SRC_W    = $clog2(REGISTERS);
localparam INPUT_SRC_W  = $clog2(REGISTERS);
localparam SOURCE_WIDTH = (REG_SRC_W > INPUT_SRC_W) ? REG_SRC_W : INPUT_SRC_W;

typedef enum logic [1:0] {
      IDLE
    , ACTIVE
    , RESTART
} core_state_t;

typedef enum logic [OPCODE_WIDTH-1:0] {
      OP_INVERT // 0 - !A
    , OP_AND    // 1 -   A & B
    , OP_NAND   // 2 - !(A & B)
    , OP_OR     // 3 -   A | B
    , OP_NOR    // 4 - !(A | B)
    , OP_XOR    // 5 -   A ^ B
    , OP_XNOR   // 6 - !(A ^ B)
    , OP_UNUSED // 7 - Unassigned
} core_op_t;

// Internal state
`DECLARE_DQ(2,            fetch_state, clk_i, rst_i, IDLE)
`DECLARE_DQ(2,            exec_state,  clk_i, rst_i, IDLE)
`DECLARE_DQ(INSTR_ADDR_W, pc,          clk_i, rst_i, {INSTR_ADDR_W{1'b0}})
`DECLARE_DQ(REGISTERS,    working,     clk_i, rst_i, {REGISTERS{1'b0}})
`DECLARE_DQ(OUTPUTS,      outputs,     clk_i, rst_i, {OUTPUTS{1'b0}})
`DECLARE_DQ(OUTPUT_IDX_W, output_idx,  clk_i, rst_i, {OUTPUT_IDX_W{1'b0}})

// Construct outputs
assign outputs_o    = outputs_q;
assign idle_o       = (fetch_state_q == IDLE && exec_state_q == IDLE);
assign instr_addr_o = pc_q;
assign instr_rd_o   = (fetch_state_q != IDLE);

// Fetch handling
always_comb begin : p_fetch
    `INIT_D(fetch_state);
    `INIT_D(pc);

    // Start/restart execution on request
    if (trigger_i) begin
        fetch_state = (fetch_state == ACTIVE) ? RESTART : ACTIVE;
        pc          = {INSTR_ADDR_W{1'b0}};

    // If active and not stalled, increment to the next PC
    end else if (fetch_state != IDLE && !instr_stall_i) begin
        fetch_state = ACTIVE;
        pc          = pc + { {(INSTR_ADDR_W-1){1'b0}}, 1'b1 };

    end

    // If all instructions are consumed, returned to idle
    if (pc == populated_i && !instr_stall_i) fetch_state = IDLE;
end

// Execution handling
always_comb begin : p_execute
    // Working variables
    core_op_t                opcode;
    logic [SOURCE_WIDTH-1:0] src_a, src_b;
    logic                    src_ip_a, src_ip_b;
    logic [REG_SRC_W-1:0   ] tgt_reg;
    logic                    gen_out;
    logic                    val_a, val_b, result;

    // Initialise state
    `INIT_D(exec_state);
    `INIT_D(working);
    `INIT_D(outputs);
    `INIT_D(output_idx);

    // On a restart request, abort execution and reset output index
    if (exec_state == ACTIVE && trigger_i) begin
        exec_state = RESTART;
        output_idx = {OUTPUT_IDX_W{1'b0}};
    // When fetch returns to ACTIVE, allow execution to resume
    end else if (exec_state == RESTART && fetch_state_q == ACTIVE) begin
        exec_state = ACTIVE;
    end

    // If execute is active, and fetch not stalled, execute
    if (exec_state == ACTIVE && !instr_stall_i) begin
        // Decode the operation
        {
            opcode,          // Operation [14:12]
            src_a, src_ip_a, // Source A + is A input/!register [11:8]
            src_b, src_ip_b, // Source B + is B input/!register [ 7:4]
            tgt_reg,         // Target register
            gen_out          // Generates output flag
        } = instr_data_i;

        // Pickup the inputs
        val_a = src_ip_a ? inputs_i[src_a] : working[src_a];
        val_b = src_ip_b ? inputs_i[src_b] : working[src_b];

        // Perform the operation
        case (opcode)
            OP_INVERT: result = ! val_a         ;
            OP_AND   : result =   val_a & val_b ;
            OP_NAND  : result = !(val_a & val_b);
            OP_OR    : result =   val_a | val_b ;
            OP_NOR   : result = !(val_a | val_b);
            OP_XOR   : result =   val_a ^ val_b ;
            OP_XNOR  : result = !(val_a ^ val_b);
            default  : result = 1'b0;
        endcase

        // Store the result
        working[tgt_reg] = result;

        // Generate an output if required
        if (gen_out) begin
            outputs[output_idx] = result;
            output_idx          = output_idx + { {(OUTPUT_IDX_W-1){1'b0}}, 1'b1 };
        end
    end

    // When transitioning to active, reset the outputs
    if (exec_state == IDLE && fetch_state_q == ACTIVE)
        output_idx = {OUTPUT_IDX_W{1'b0}};

    // Copy the fetch state to inform the next execute cycle
    if (!instr_stall_i && exec_state != RESTART) begin
        exec_state = fetch_state_q;
    end
end

endmodule : nx_node_core
