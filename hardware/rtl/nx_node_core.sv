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

// nx_node_core
// Evaluates instruction sequence against input values and internal register
// state to produce outputs
//
module nx_node_core #(
      parameter INPUTS       =   8 // Number of input signals
    , parameter OUTPUTS      =   8 // Number of output signals
    , parameter REGISTERS    =   8 // Number of internal registers
    , parameter MAX_INSTRS   = 512 // Maximum instructions
    , parameter INSTR_WIDTH  =  15 // Width of each instruction
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
localparam INSTR_ADDR_W    = $clog2(MAX_INSTRS);
localparam REGISTER_IDX_W  = $clog2(REGISTERS);
localparam OUTPUT_IDX_W    = $clog2(OUTPUTS);
localparam MAX_IR_COUNT    = (INPUTS  > REGISTERS) ? INPUTS : REGISTERS;
localparam INPUT_REPEAT    = MAX_IR_COUNT / INPUTS;
localparam REGISTER_REPEAT = MAX_IR_COUNT / REGISTERS;

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
`DECLARE_DQ(1,            restart_req, clk_i, rst_i, 1'b0)
`DECLARE_DQ(1,            fetch_idle,  clk_i, rst_i, 1'b1)
`DECLARE_DQ(1,            decode_idle, clk_i, rst_i, 1'b1)
`DECLARE_DQ(1,            exec_idle,   clk_i, rst_i, 1'b1)
`DECLARE_DQ(3,            fetch_first, clk_i, rst_i, 3'd0)
`DECLARE_DQ(INSTR_ADDR_W, pc,          clk_i, rst_i, {INSTR_ADDR_W{1'b0}})
`DECLARE_DQ(REGISTERS,    working,     clk_i, rst_i, {REGISTERS{1'b0}})
`DECLARE_DQ(OUTPUTS,      outputs,     clk_i, rst_i, {OUTPUTS{1'b0}})
`DECLARE_DQ(OUTPUT_IDX_W, output_idx,  clk_i, rst_i, {OUTPUT_IDX_W{1'b0}})

// Create expanded versions of signals
logic [MAX_IR_COUNT-1:0] exp_inputs, exp_working;
assign exp_inputs  = {INPUT_REPEAT{inputs_i}};
assign exp_working = {REGISTER_REPEAT{working}};

// Construct outputs
assign outputs_o    = outputs_q;
assign idle_o       = fetch_idle_q && decode_idle_q && exec_idle_q;
assign instr_addr_o = pc_q;
assign instr_rd_o   = !fetch_idle_q;

// Fetch handling
always_comb begin : p_fetch
    `INIT_D(restart_req);
    `INIT_D(fetch_idle);
    `INIT_D(fetch_first);
    `INIT_D(pc);

    // Rotate fetch first as long as not stalled
    if (!instr_stall_i) fetch_first = { fetch_first[1:0], 1'b0 };

    // If a trigger is seen, raise restart request
    if (trigger_i) restart_req = 1'b1;

    // If inactive, and restart request seen, start fetch
    if (fetch_idle && restart_req) begin
        fetch_idle     = 1'b0;
        restart_req    = 1'b0;
        pc             = {INSTR_ADDR_W{1'b0}};
        fetch_first[0] = 1'b1;

    // Otherwise, if active and not stalled, fetch the next instruction
    end else if (!fetch_idle && !instr_stall_i) begin
        pc = pc + { {(INSTR_ADDR_W-1){1'b0}}, 1'b1 };

    end

    // If all instructions are consumed, returned to idle
    if (pc == populated_i && !instr_stall_i) fetch_idle = 1'b1;
end

// Execution handling
`DECLARE_DQT(nx_instruction_t, decoded, clk_i, rst_i, {$bits(nx_instruction_t){1'b0}})

always_comb begin : p_execute
    // Working state
    logic val_a, val_b, result;
    { val_a, val_b, result }  = 'd0;

    // Decode state
    `INIT_D(decode_idle);
    `INIT_D(decoded);

    // Initialise state
    `INIT_D(exec_idle);
    `INIT_D(working);
    `INIT_D(outputs);
    `INIT_D(output_idx);

    // If this is a first fetch, reset output index
    if (fetch_first_q[2]) output_idx = {OUTPUT_IDX_W{1'b0}};

    // If fetch is not stalled
    if (!instr_stall_i) begin

        // Execute the previously decoded instruction
        if (!exec_idle) begin
            // Pickup the inputs
            val_a = (
                decoded.src_a_ip ? exp_inputs[decoded.src_a]
                                 : exp_working[decoded.src_a]
            );
            val_b = (
                decoded.src_b_ip ? exp_inputs[decoded.src_b]
                                 : exp_working[decoded.src_b]
            );

            // Perform the operation
            case (decoded.opcode)
                NX_OP_INVERT: result = ! val_a         ;
                NX_OP_AND   : result =   val_a & val_b ;
                NX_OP_NAND  : result = !(val_a & val_b);
                NX_OP_OR    : result =   val_a | val_b ;
                NX_OP_NOR   : result = !(val_a | val_b);
                NX_OP_XOR   : result =   val_a ^ val_b ;
                NX_OP_XNOR  : result = !(val_a ^ val_b);
                default     : result = 1'b0;
            endcase

            // Store the result
            working[decoded.tgt_reg[REGISTER_IDX_W-1:0]] = result;

            // Generate an output if required
            if (decoded.gen_out) begin
                outputs[output_idx] = result;
                output_idx          = output_idx + { {(OUTPUT_IDX_W-1){1'b0}}, 1'b1 };
            end
        end

        // Decode the next instruction returned from the RAM
        if (!decode_idle) begin
            decoded = instr_data_i[$bits(nx_instruction_t)-1:0];
        end

        // Propagate idle state
        exec_idle   = decode_idle;
        decode_idle = fetch_idle_q;

    end

end

endmodule : nx_node_core
