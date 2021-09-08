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
      parameter INPUTS    = 32 // Number of input signals
    , parameter OUTPUTS   = 32 // Number of output signals
    , parameter REGISTERS =  8 // Number of internal registers
) (
      input  logic                          clk_i
    , input  logic                          rst_i
    // I/O from simulated logic
    , input  logic [            INPUTS-1:0] inputs_i      // Input vector
    , output logic [           OUTPUTS-1:0] outputs_o     // Output vector
    // Execution controls
    , input  logic [$clog2(MAX_NODE_INSTRS)-1:0] populated_i   // # of populated instructions
    , input  logic                               trigger_i     // Trigger execution
    , output logic                               idle_o        // Core idle flag
    // Instruction fetch
    , output logic [$clog2(MAX_NODE_INSTRS)-1:0] instr_addr_o  // Instruction fetch address
    , output logic                               instr_rd_o    // Read enable
    , input  instruction_t                       instr_data_i  // Instruction data
    , input  logic                               instr_stall_i // Fetch stall
);

// Parameters
localparam INSTR_ADDR_W    = $clog2(MAX_NODE_INSTRS);
localparam INPUT_IDX_W     = $clog2(INPUTS);
localparam OUTPUT_IDX_W    = $clog2(OUTPUTS);
localparam REGISTER_IDX_W  = $clog2(REGISTERS);

typedef enum logic [1:0] {
      IDLE
    , ACTIVE
    , RESTART
} core_state_t;

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
`DECLARE_DQT(instruction_t, decoded, clk_i, rst_i, 'd0)

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
                decoded.src_a_ip ? inputs_i[decoded.src_a[INPUT_IDX_W-1:0]]
                                 : working[decoded.src_a[REGISTER_IDX_W-1:0]]
            );
            val_b = (
                decoded.src_b_ip ? inputs_i[decoded.src_b[INPUT_IDX_W-1:0]]
                                 : working[decoded.src_b[REGISTER_IDX_W-1:0]]
            );

            // Perform the operation
            case (decoded.opcode)
                OPERATION_INVERT: result = ! val_a         ;
                OPERATION_AND   : result =   val_a & val_b ;
                OPERATION_NAND  : result = !(val_a & val_b);
                OPERATION_OR    : result =   val_a | val_b ;
                OPERATION_NOR   : result = !(val_a | val_b);
                OPERATION_XOR   : result =   val_a ^ val_b ;
                OPERATION_XNOR  : result = !(val_a ^ val_b);
                default         : result = 1'b0;
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
        if (!decode_idle) decoded = instr_data_i;

        // Propagate idle state
        exec_idle   = decode_idle;
        decode_idle = fetch_idle_q;

    end

end

endmodule : nx_node_core
