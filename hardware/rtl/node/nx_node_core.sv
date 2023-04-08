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
import NXISA::*;
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
`DECLARE_DQ(1, stall, i_clk, i_rst, 'd1)
`DECLARE_DQ(1, pause, i_clk, i_rst, 'd1)
`DECLARE_DQ(1, idle,  i_clk, i_rst, 'd1)
`DECLARE_DQ(1, pc0,   i_clk, i_rst, 'd1)

// Program counter
`DECLARE_DQT(pc_t, fetch_pc,    i_clk, i_rst, 'd0)
`DECLARE_DQ (   1, fetch_valid, i_clk, i_rst, 'd0)

// Register file
`DECLARE_DQ_ARRAY(REG_WIDTH, REG_COUNT, regfile, i_clk, i_rst, 'd0)

// === Decode ===
logic dcd_valid;
logic dcd_is_memory;

`DECLARE_DQ(1, dcd_is_pause,   i_clk, i_rst, 'd0)
`DECLARE_DQ(1, dcd_is_truth,   i_clk, i_rst, 'd0)
`DECLARE_DQ(1, dcd_is_pick,    i_clk, i_rst, 'd0)
`DECLARE_DQ(1, dcd_is_shuffle, i_clk, i_rst, 'd0)
`DECLARE_DQ(1, dcd_is_load,    i_clk, i_rst, 'd0)
`DECLARE_DQ(1, dcd_is_store,   i_clk, i_rst, 'd0)
`DECLARE_DQ(1, dcd_is_send,    i_clk, i_rst, 'd0)

`DECLARE_DQ(        8, dcd_val_a,   i_clk, i_rst, 'd0)
`DECLARE_DQ(        8, dcd_val_b,   i_clk, i_rst, 'd0)
`DECLARE_DQ(        8, dcd_val_c,   i_clk, i_rst, 'd0)
`DECLARE_DQ(        8, dcd_val_7,   i_clk, i_rst, 'd0)
`DECLARE_DQ(REG_IDX_W, dcd_tgt_reg, i_clk, i_rst, 'd0)
`DECLARE_DQ(        1, dcd_ovr_a,   i_clk, i_rst, 'd0)
`DECLARE_DQ(        1, dcd_ovr_b,   i_clk, i_rst, 'd0)
`DECLARE_DQ(        1, dcd_ovr_c,   i_clk, i_rst, 'd0)
`DECLARE_DQ(        1, dcd_fwd_a,   i_clk, i_rst, 'd0)
`DECLARE_DQ(        1, dcd_fwd_b,   i_clk, i_rst, 'd0)
`DECLARE_DQ(        1, dcd_fwd_c,   i_clk, i_rst, 'd0)
`DECLARE_DQ(        1, dcd_fwd_7,   i_clk, i_rst, 'd0)

`DECLARE_DQ(4, dcd_addr_10_7, i_clk, i_rst, 'd0)

`DECLARE_DQT(instruction_t, dcd_instr, i_clk, i_rst, 'd0)

`DECLARE_DQ(2, dcd_slot, i_clk, i_rst, 'd0)

// === Execute ===

logic [7:0] exe_rd_data;
logic [7:0] exe_val_a, exe_val_b, exe_val_c, exe_val_7;
logic [9:0] exe_full_addr;
logic [7:0] exe_result_truth, exe_result_shuffle;
logic [2:0] exe_truth_select;
logic       exe_truth_output;

node_id_t     exe_msg_tgt;
node_header_t exe_msg_hdr;
node_signal_t exe_msg_sig;

`DECLARE_DQG(REG_IDX_W, exe_tgt_reg,    i_clk, i_rst, 'd0, ~stall)
`DECLARE_DQG(        1, exe_cmt_rd,     i_clk, i_rst, 'd0, ~stall)
`DECLARE_DQG(        1, exe_cmt_result, i_clk, i_rst, 'd0, ~stall)
`DECLARE_DQG(        2, exe_rd_slot,    i_clk, i_rst, 'd0, ~stall)
`DECLARE_DQG(        8, exe_result,     i_clk, i_rst, 'd0, ~stall)

`DECLARE_DQTG(node_message_t, exe_message, i_clk, i_rst, 'd0, ~stall)
`DECLARE_DQG (             1, exe_send,    i_clk, i_rst, 'd0, ~stall)

`DECLARE_DQ(10, exe_mem_addr, i_clk, i_rst, 'd0)
`DECLARE_DQ( 8, exe_wr_data,  i_clk, i_rst, 'd0)
`DECLARE_DQ(32, exe_wr_strb,  i_clk, i_rst, 'd0)

// === Commit ===

logic       cmt_valid;
logic [7:0] cmt_value;

// =============================================================================
// Expose Idle Flag
// =============================================================================

assign o_idle = idle_q;

// =============================================================================
// Slot
// =============================================================================

assign slot = (i_trigger && pause_q) ? (~slot_q) : slot_q;

assign o_slot = slot_q;

// =============================================================================
// Fetch
// =============================================================================

// Determine stall condition
assign stall = pause_q ||
               (o_send_valid && !i_send_ready) ||
               (dcd_is_load_q && (|exe_wr_strb_q));

// If stalled either hold PC or reset to zero, else always increment
always_comb begin : comb_fetch_pc
    fetch_pc = fetch_pc_q;
    // If PC0 specified, force
    if (pc0_q) begin
        fetch_pc = 'd0;
    // If entering stall, backup two cycles
    end else if (!stall_q && stall) begin
        fetch_pc = fetch_pc_q - 'd2;
    // Otherwise, if not stalling, increment
    end else if (!stall_q) begin
        fetch_pc = fetch_pc_q + 'd1;
    end
end

// Drive RAM interface
assign o_inst_addr  = fetch_pc_q;
assign o_inst_rd_en = !stall_q;

// Pipeline read signal as instruction valid
assign fetch_valid = o_inst_rd_en && !stall;

// =============================================================================
// Decode
// =============================================================================

// Take account of the stall
assign dcd_valid = fetch_valid_q && !stall;

// Type cast raw data onto the instruction union
assign dcd_instr = i_inst_rd_data;

// Operation decode
assign dcd_is_pause   = dcd_valid && (dcd_instr.memory.op == NXISA::OP_PAUSE );
assign dcd_is_memory  = dcd_valid && (dcd_instr.memory.op == NXISA::OP_MEMORY);
assign dcd_is_truth   = dcd_valid && (dcd_instr.memory.op == NXISA::OP_TRUTH );
assign dcd_is_pick    = dcd_valid && (dcd_instr.memory.op == NXISA::OP_PICK  );
assign dcd_is_shuffle = dcd_valid && ((dcd_instr.memory.op == NXISA::OP_SHUFFLE    ) ||
                                      (dcd_instr.memory.op == NXISA::OP_SHUFFLE_ALT));
assign dcd_is_load    = dcd_is_memory && (dcd_instr.memory.mode == NXISA::MEM_LOAD );
assign dcd_is_store   = dcd_is_memory && (dcd_instr.memory.mode == NXISA::MEM_STORE);
assign dcd_is_send    = dcd_is_memory && (dcd_instr.memory.mode == NXISA::MEM_SEND );

// Select the right value for each register (with register forwarding)
assign dcd_val_a = (cmt_valid && exe_tgt_reg_q == dcd_instr.truth.src_a)
                   ? cmt_value
                   : regfile_q[dcd_instr.truth.src_a];
assign dcd_val_b = (cmt_valid && exe_tgt_reg_q == dcd_instr.truth.src_b)
                   ? cmt_value
                   : regfile_q[dcd_instr.truth.src_b];
assign dcd_val_c = (cmt_valid && exe_tgt_reg_q == dcd_instr.truth.src_c)
                   ? cmt_value
                   : regfile_q[dcd_instr.truth.src_c];

// Special case for R7 which is only used by the TRUTH instruction
assign dcd_val_7 = (cmt_valid && exe_tgt_reg_q == 'd7) ? cmt_value : regfile_q[7];

// Forward the target register through
assign dcd_tgt_reg = dcd_is_truth ? 'd7 : dcd_instr.memory.tgt;

// Flag if a pending read means value needs to be overridden by read data
assign dcd_ovr_a = dcd_is_load_q && (dcd_tgt_reg_q == dcd_instr.truth.src_a);
assign dcd_ovr_b = dcd_is_load_q && (dcd_tgt_reg_q == dcd_instr.truth.src_b);
assign dcd_ovr_c = dcd_is_load_q && (dcd_tgt_reg_q == dcd_instr.truth.src_c);

// Flag if a pending read means value needs to be overridden by execute result
assign dcd_fwd_a = ((dcd_is_shuffle_q && (dcd_instr.truth.src_a == dcd_tgt_reg_q)) ||
                    (dcd_is_truth_q   && (dcd_instr.truth.src_a == 'd7          )));
assign dcd_fwd_b = ((dcd_is_shuffle_q && (dcd_instr.truth.src_b == dcd_tgt_reg_q)) ||
                    (dcd_is_truth_q   && (dcd_instr.truth.src_b == 'd7          )));
assign dcd_fwd_c = ((dcd_is_shuffle_q && (dcd_instr.truth.src_c == dcd_tgt_reg_q)) ||
                    (dcd_is_truth_q   && (dcd_instr.truth.src_c == 'd7          )));
assign dcd_fwd_7 = dcd_is_truth_q;

// Determine address [10:7]
// NOTE: PICK operations offset by 64 rows (shifted by one for the 16-bit slot)
assign dcd_addr_10_7 = dcd_is_memory ? dcd_instr.memory.address_10_7 : 'd1;

// Determine the 8-bit slot selector
always_comb begin : comb_full_slot
    dcd_slot[1] = dcd_instr.memory.address_6_0[0];
    case (dcd_instr.memory.slot)
        NXISA::SLOT_PRESERVE: dcd_slot[0] =  slot_q;
        NXISA::SLOT_INVERSE : dcd_slot[0] = ~slot_q;
        NXISA::SLOT_LOWER   : dcd_slot[0] =     'd0;
        NXISA::SLOT_UPPER   : dcd_slot[0] =     'd1;
    endcase
end

// =============================================================================
// Execute
// =============================================================================

// Extract the right 8-bit slot from read data (one cycle later)
assign exe_rd_data = (exe_rd_slot_q == 'd3) ? i_data_rd_data[31:24] :
                     (exe_rd_slot_q == 'd2) ? i_data_rd_data[23:16] :
                     (exe_rd_slot_q == 'd1) ? i_data_rd_data[15: 8]
                                            : i_data_rd_data[ 7: 0];

// Override register value with read data or forwarded value if required
// NOTE: Read data forwarding is only supported for the first register (A)
assign exe_val_a = dcd_ovr_a_q ? exe_rd_data :
                   dcd_fwd_a_q ? exe_result_q
                               : dcd_val_a_q;
assign exe_val_b = dcd_fwd_b_q ? exe_result_q
                               : dcd_val_b_q;
assign exe_val_c = dcd_fwd_c_q ? exe_result_q
                               : dcd_val_c_q;
assign exe_val_7 = dcd_fwd_7_q ? exe_result_q
                               : dcd_val_7_q;

// Form the full 10-bit address
assign exe_full_addr = { dcd_addr_10_7_q, dcd_instr_q.memory.address_6_0[6:1] };

// Pipeline the target register
assign exe_tgt_reg = dcd_tgt_reg_q;

// Determine what type of commit is required
assign exe_cmt_rd     = dcd_is_load_q;
assign exe_cmt_result = dcd_is_truth_q || dcd_is_shuffle_q;

// === PAUSE ===
// - Activate pause when requested
assign pause = (pause_q && !i_trigger) || dcd_is_pause_q;
// - If required, set the IDLE flag
assign idle = (idle_q && !i_trigger) || (dcd_is_pause_q && dcd_instr_q.pause.idle);
// - If required, reset PC to zero
assign pc0 = (pc0_q && !i_trigger) || (dcd_is_pause_q && dcd_instr_q.pause.pc0);

// === LOAD, STORE & PICK ===
// Remember the slot data is being loaded to
assign exe_rd_slot = dcd_slot_q;

assign exe_mem_addr = exe_full_addr;
assign exe_wr_data  = dcd_is_store_q ? exe_val_a : {2{exe_result_shuffle[3:0]}};
assign exe_wr_strb  = {32{~(stall || stall_q)}} & (
    {
        24'd0, ((
                    {
                        {4{(dcd_is_pick_q &&  dcd_instr_q.pick.upper)}},
                        {4{(dcd_is_pick_q && !dcd_instr_q.pick.upper)}}
                    } & {
                        dcd_instr_q.pick.mask,
                        dcd_instr_q.pick.mask
                    }
                ) | (
                    {8{dcd_is_store_q}} & {dcd_instr_q.memory.send_row,
                                           dcd_instr_q.memory.send_col}
                ))
    } << {dcd_slot_q, 3'd0}
);

// Drive the memory interface
assign o_data_addr    = (|exe_wr_strb_q) ? exe_mem_addr_q : exe_full_addr;
assign o_data_rd_en   = dcd_is_load_q && !stall;
assign o_data_wr_data = {4{exe_wr_data_q}};
assign o_data_wr_strb = exe_wr_strb_q;

// === SEND ===
// Form the target ID
assign exe_msg_tgt.row    = dcd_instr_q.memory.send_row;
assign exe_msg_tgt.column = dcd_instr_q.memory.send_col;

// Form the header
assign exe_msg_hdr.target     = exe_msg_tgt;
assign exe_msg_hdr.command    = NODE_COMMAND_SIGNAL;
assign exe_msg_hdr._padding_0 = 'd0;

// Form the message
assign exe_msg_sig.header  = exe_msg_hdr;
assign exe_msg_sig.address = { exe_full_addr, dcd_slot_q[1] };
assign exe_msg_sig.slot    = `TYPE_CAST(memory_slot_t, dcd_instr_q.memory.slot);
assign exe_msg_sig.data    = exe_val_a;

assign {exe_message, exe_send} = (
    (exe_send_q && !i_send_ready) ? {exe_message_q, 1'b1                                }
                                  : {exe_msg_sig,   dcd_is_send_q && ~(stall || stall_q)}
);

// Drive message interface
assign o_send_data  = exe_message_q;
assign o_send_valid = exe_send_q;

// === TRUTH ===
// - Perform multiple register bit extractions (for TRUTH)
assign exe_truth_select[0] = exe_val_a[dcd_instr_q.truth.mux_0];
assign exe_truth_select[1] = exe_val_b[dcd_instr_q.truth.mux_1];
assign exe_truth_select[2] = exe_val_c[dcd_instr_q.truth.mux_2];
// - Calculate result
always_comb begin : comb_truth
    logic [6:0] _unused_shifted;
    {_unused_shifted, exe_truth_output} = (dcd_instr_q.truth.truth >> exe_truth_select);
end
// - Shift result into register 7
assign exe_result_truth = { exe_val_7[6:0], exe_truth_output };

// === SHUFFLE ===
assign exe_result_shuffle[0] = exe_val_a[dcd_instr_q.shuffle.mux_0];
assign exe_result_shuffle[1] = exe_val_a[dcd_instr_q.shuffle.mux_1];
assign exe_result_shuffle[2] = exe_val_a[dcd_instr_q.shuffle.mux_2];
assign exe_result_shuffle[3] = exe_val_a[dcd_instr_q.shuffle.mux_3];
assign exe_result_shuffle[4] = exe_val_a[dcd_instr_q.shuffle.mux_4];
assign exe_result_shuffle[5] = exe_val_a[dcd_instr_q.shuffle.mux_5];
assign exe_result_shuffle[6] = exe_val_a[dcd_instr_q.shuffle.mux_6];
assign exe_result_shuffle[7] = exe_val_a[dcd_instr_q.shuffle.mux_7];

// Select the right result
assign exe_result = dcd_is_truth_q ? exe_result_truth : exe_result_shuffle;

// =============================================================================
// Commit
// =============================================================================

// Determine if a value needs to be written
assign cmt_valid = exe_cmt_rd_q || exe_cmt_result_q;

// Resolve whether the commit value comes from read data or the execute result
assign cmt_value = exe_cmt_rd_q ? exe_rd_data : exe_result_q;

// Update register values
generate
for (genvar idx = 0; idx < 8; idx++) begin : gen_register_update
    assign regfile[idx] = (cmt_valid && exe_tgt_reg_q == idx[2:0]) ? cmt_value : regfile_q[idx];
end
endgenerate

// =============================================================================
// Unused
// =============================================================================

logic _unused;
assign _unused = &{ 1'b0, dcd_val_7_q[7] };

endmodule : nx_node_core
