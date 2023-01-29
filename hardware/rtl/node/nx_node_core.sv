// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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
// Execution core of each node that evaluates the instruction sequence
//
module nx_node_core
import NXConstants::*;
#(
      localparam RAM_ADDR_W = 10
    , localparam RAM_DATA_W = 32
) (
      input  logic                  i_clk
    , input  logic                  i_rst
    // Control signals
    , output logic                  o_idle
    , input  logic                  i_trigger
    , output logic                  o_slot
    // Instruction RAM
    , output logic [RAM_ADDR_W-1:0] o_inst_addr
    , output logic                  o_inst_rd_en
    , input  logic [RAM_DATA_W-1:0] i_inst_rd_data
    // Data RAM
    , output logic [RAM_ADDR_W-1:0] o_data_addr
    , output logic [RAM_DATA_W-1:0] o_data_wr_data
    , output logic [RAM_DATA_W-1:0] o_data_wr_strb
    , output logic                  o_data_rd_en
    , input  logic [RAM_DATA_W-1:0] i_data_rd_data
    // Outbound messages
    , output node_message_t         o_send_data
    , output logic                  o_send_valid
    , input  logic                  i_send_ready
);

localparam REG_COUNT = 8;
localparam REG_WIDTH = 8;
localparam REG_IDX_W = $clog2(REG_COUNT);

typedef logic [RAM_ADDR_W-1:0] pc_t;

// =============================================================================
// Signals
// =============================================================================

// Slot
`DECLARE_DQ(1, slot, i_clk, i_rst, 'd1)

// Stall handling
logic stall;
`DECLARE_DQ(1, pause, i_clk, i_rst, 'd1)
`DECLARE_DQ(1, idle,  i_clk, i_rst, 'd1)
`DECLARE_DQ(1, pc0,   i_clk, i_rst, 'd1)

// Program counter
`DECLARE_DQT(pc_t, pc_fetch,   i_clk, i_rst, 'd0)
`DECLARE_DQT(pc_t, pc_execute, i_clk, i_rst, 'd0)

// Decode
NXISA::instruction_t instruction;
logic                is_pause, is_memory, is_load, is_store, is_send, is_truth,
                     is_pick, is_shuffle;

// Registers
`DECLARE_DQ_ARRAY(REG_WIDTH, REG_COUNT, regfile, i_clk, i_rst, 'd0)
logic [REG_WIDTH-1:0] reg_rd_data;
logic [REG_WIDTH-1:0] reg_forward [REG_COUNT-1:0];
logic [REG_WIDTH-1:0] src_a, src_b, src_c;
logic [REG_WIDTH-1:0] muxsel;

// Memory
`DECLARE_DQ(        1, rd_pend,        i_clk, i_rst, 'd0)
`DECLARE_DQ(REG_IDX_W, rd_pend_target, i_clk, i_rst, 'd0)
`DECLARE_DQ(        2, rd_pend_slot,   i_clk, i_rst, 'd0)

NXISA::f_address_10_7_t addr_10_7;
NXISA::f_address_6_0_t  addr_6_0;
logic [RAM_ADDR_W-1:0]  full_addr;
logic [           1:0]  full_slot;

// Truth
logic [2:0] truth_select;
logic       truth_result;

// Messages
`DECLARE_DQT(node_message_t, send_msg, i_clk, i_rst, 'd0)
`DECLARE_DQ (             1, send_vld, i_clk, i_rst, 'd0)
node_signal_t to_send;

// =============================================================================
// Slot
// =============================================================================

assign slot = (i_trigger && idle_q) ? (~slot_q) : slot_q;

assign o_slot = slot_q;

// =============================================================================
// Fetch
// =============================================================================

// Determine stall condition
assign stall = pause_q || (o_send_valid && !i_send_ready);

// If stalled either hold PC or reset to zero, else always increment
assign pc_fetch = stall ? (pc0_q ? 'd0 : pc_fetch_q)
                        : (pc_fetch_q + 'd1);

// Drive RAM interface
assign o_inst_addr  = pc_fetch;
assign o_inst_rd_en = !pause;

// =============================================================================
// Decode
// =============================================================================

// Pickup PC from fetch
assign pc_execute = stall ? pc_execute_q : pc_fetch_q;

// Type cast raw data onto the instruction union
assign instruction = NXISA::instruction_t'(i_inst_rd_data);

// Identify the operation
assign is_pause   = (!pause_q) && (instruction.memory.op == NXISA::OP_PAUSE );
assign is_memory  = (!pause_q) && (instruction.memory.op == NXISA::OP_MEMORY);
assign is_truth   = (!pause_q) && (instruction.memory.op == NXISA::OP_TRUTH );
assign is_pick    = (!pause_q) && (instruction.memory.op == NXISA::OP_PICK  );
assign is_shuffle = (!pause_q) && ((instruction.memory.op == NXISA::OP_SHUFFLE) ||
                                   (instruction.memory.op == NXISA::OP_SHUFFLE_ALT));
assign is_load    = is_memory && (instruction.memory.mode == NXISA::MEM_LOAD );
assign is_store   = is_memory && (instruction.memory.mode == NXISA::MEM_STORE);
assign is_send    = is_memory && (instruction.memory.mode == NXISA::MEM_SEND );

// =============================================================================
// Register Reads
// =============================================================================

// Extract the right 8-bit slot from read data
assign reg_rd_data = (rd_pend_slot_q == 'd3) ? i_data_rd_data[31:24] :
                     (rd_pend_slot_q == 'd2) ? i_data_rd_data[23:16] :
                     (rd_pend_slot_q == 'd1) ? i_data_rd_data[15: 8]
                                             : i_data_rd_data[ 7: 0];

// R7 only acts as a shift register for TRUTH operations, so forwarding impossible
assign reg_forward[REG_COUNT-1] = regfile_q[REG_COUNT-1];

// R0-R6 require register forwarding
always_comb begin : comb_forwarding
    for (int idx = 0; idx < (REG_COUNT - 1); idx++) begin
        reg_forward[idx] = (
            (rd_pend_q && (rd_pend_target_q == idx[2:0])) ? reg_rd_data : regfile_q[idx]
        );
    end
end

// Pickup the source registers (for MEMORY, TRUTH, PICK, and SHUFFLE)
assign src_a = reg_forward[instruction.truth.src_a];
assign src_b = reg_forward[instruction.truth.src_b];
assign src_c = reg_forward[instruction.truth.src_c];

// Perform single register bit extractions (for PICK and SHUFFLE)
assign muxsel[0] = src_a[instruction.shuffle.mux_0];
assign muxsel[1] = src_a[instruction.shuffle.mux_1];
assign muxsel[2] = src_a[instruction.shuffle.mux_2];
assign muxsel[3] = src_a[instruction.shuffle.mux_3];
assign muxsel[4] = src_a[instruction.shuffle.mux_4];
assign muxsel[5] = src_a[instruction.shuffle.mux_5];
assign muxsel[6] = src_a[instruction.shuffle.mux_6];
assign muxsel[7] = src_a[instruction.shuffle.mux_7];

// =============================================================================
// Register Writes
// NOTE: Only R0-R6 are directly writeable, R7 is a shift register for TRUTH
// =============================================================================

always_comb begin : comb_reg_write
    for (int idx = 0; idx < (REG_COUNT - 1); idx++) begin
        // SHUFFLE is the only operation which can directly write to a register
        if (is_shuffle && (instruction.shuffle.tgt == idx[2:0])) begin
            regfile[idx] = muxsel;
        // LOAD operations write to registers a cycle later (RAM latency)
        end else if (rd_pend_q && (rd_pend_target_q == idx[2:0])) begin
            regfile[idx] = reg_rd_data;
        // Otherwise hold the current value
        end else begin
            regfile[idx] = regfile_q[idx];
        end
    end
end

// =============================================================================
// Stalling/Pausing
// =============================================================================

// Activate pause when requested
assign pause = (pause_q && !i_trigger) || is_pause;

// If required, set the IDLE flag
assign idle = (idle_q && !i_trigger) || (is_pause && instruction.pause.idle);

// If required, reset PC to zero
assign pc0 = (pc0_q && !i_trigger) || (is_pause && instruction.pause.pc0);

// Expose idle
assign o_idle = idle_q;

// =============================================================================
// Reading/Writing Local Memory
// =============================================================================

// Calculate the full memory address
// NOTE: PICK operations offset by 64 rows (shifted by one for the 16-bit slot)
assign addr_10_7 = is_memory ? instruction.memory.address_10_7 : 'd1;
assign addr_6_0  = instruction.memory.address_6_0;
assign full_addr = { addr_10_7, addr_6_0[6:1] };

always_comb begin : comb_full_slot
    full_slot[1] = addr_6_0[0];
    case (instruction.memory.slot)
        NXISA::SLOT_PRESERVE: full_slot[0] =  slot_q;
        NXISA::SLOT_INVERSE : full_slot[0] = ~slot_q;
        NXISA::SLOT_LOWER   : full_slot[0] =     'd0;
        NXISA::SLOT_UPPER   : full_slot[0] =     'd1;
    endcase
end

// Drive data interface
assign o_data_addr    = full_addr;
assign o_data_wr_data = is_store ? {4{src_a}} : {8{muxsel[3:0]}};
assign o_data_rd_en   = is_load;
assign o_data_wr_strb = (
    {24'd0, {
        {4{(is_pick &&  instruction.pick.upper) || is_store}},
        {4{(is_pick && !instruction.pick.upper) || is_store}}
    }} << {full_slot, 3'd0}
);

// Track pending read
assign rd_pend        = is_load;
assign rd_pend_target = instruction.memory.tgt;
assign rd_pend_slot   = full_slot;

// =============================================================================
// Truth Table
// =============================================================================

// Perform multiple register bit extractions (for TRUTH)
assign truth_select[0] = src_a[instruction.truth.mux_0];
assign truth_select[1] = src_b[instruction.truth.mux_1];
assign truth_select[2] = src_c[instruction.truth.mux_2];

// Calculate result
assign truth_result = instruction.truth.truth[truth_select];

// Shift result into register 7
assign regfile[7] = is_truth ? { regfile_q[7][7:1], truth_result }
                             : regfile_q[7];

// =============================================================================
// Send Message
// =============================================================================

assign to_send.header.command       = NODE_COMMAND_SIGNAL;
assign to_send.header.target.column = instruction.memory.send_col;
assign to_send.header.target.row    = instruction.memory.send_row;
assign to_send.address              = {addr_10_7, addr_6_0};
assign to_send.slot                 = instruction.memory.slot;
assign to_send.data                 = src_a;

assign {send_msg, send_vld} = (
    (send_vld_q && !i_send_ready) ? {send_msg_q, 1'b1   }
                                  : {to_send,    is_send}
);

// Drive message interface
assign o_send_data  = send_msg_q;
assign o_send_valid = send_vld_q;

endmodule : nx_node_core
