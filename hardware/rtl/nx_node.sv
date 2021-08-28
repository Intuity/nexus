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

// nx_node
// A single logic node with inbound and outbound message interfaces, ready to be
// tiled into a grid
//
module nx_node #(
      parameter ADDR_ROW_WIDTH  =   4
    , parameter ADDR_COL_WIDTH  =   4
    , parameter INSTR_WIDTH     =  21
    , parameter INPUTS          =  32
    , parameter OUTPUTS         =  32
    , parameter REGISTERS       =   8
    , parameter MAX_INSTRS      = 512
    , parameter OPCODE_WIDTH    =   3
    , parameter OP_STORE_LENGTH = 512
    , parameter OP_STORE_WIDTH  = 1 + ADDR_ROW_WIDTH + ADDR_COL_WIDTH + $clog2(INPUTS) + 1
) (
      input  logic clk_i
    , input  logic rst_i
    // Control signals
    , input  logic                      trigger_i
    , output logic                      idle_o
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
    // Channel tokens
    , input  logic token_grant_i
    , output logic token_release_o
    // Inbound interfaces
    // - North
    , input  nx_message_t ib_north_data_i
    , input  logic        ib_north_valid_i
    , output logic        ib_north_ready_o
    // - East
    , input  nx_message_t ib_east_data_i
    , input  logic        ib_east_valid_i
    , output logic        ib_east_ready_o
    // - South
    , input  nx_message_t ib_south_data_i
    , input  logic        ib_south_valid_i
    , output logic        ib_south_ready_o
    // - West
    , input  nx_message_t ib_west_data_i
    , input  logic        ib_west_valid_i
    , output logic        ib_west_ready_o
    // Outbound interfaces
    // - North
    , output nx_message_t ob_north_data_o
    , output logic        ob_north_valid_o
    , input  logic        ob_north_ready_i
    , input  logic        ob_north_present_i
    // - East
    , output nx_message_t ob_east_data_o
    , output logic        ob_east_valid_o
    , input  logic        ob_east_ready_i
    , input  logic        ob_east_present_i
    // - South
    , output nx_message_t ob_south_data_o
    , output logic        ob_south_valid_o
    , input  logic        ob_south_ready_i
    , input  logic        ob_south_present_i
    // - West
    , output nx_message_t ob_west_data_o
    , output logic        ob_west_valid_o
    , input  logic        ob_west_ready_i
    , input  logic        ob_west_present_i
);

// -----------------------------------------------------------------------------
// Idle Control
// -----------------------------------------------------------------------------
logic core_idle, decode_idle, ctrl_idle, dist_idle;

`DECLARE_DQ(1, idle, clk_i, rst_i, 1'b0)

assign idle = (
    core_idle && decode_idle && dist_idle && ctrl_idle &&
    !dcd_valid && !byp_valid && !outbound_valid
);

assign idle_o = idle_q;

// -----------------------------------------------------------------------------
// Arbiter
// -----------------------------------------------------------------------------

nx_message_t   dcd_data,  byp_data;
logic          dcd_valid, dcd_ready, byp_valid, byp_ready;
nx_direction_t byp_dir;

nx_stream_arbiter #(
      .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
) inbound_arb (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Control signals
    , .node_row_i(node_row_i )
    , .node_col_i(node_col_i )
    // Inbound message streams
    // - North
    , .north_data_i (ib_north_data_i )
    , .north_valid_i(ib_north_valid_i)
    , .north_ready_o(ib_north_ready_o)
    // - East
    , .east_data_i (ib_east_data_i )
    , .east_valid_i(ib_east_valid_i)
    , .east_ready_o(ib_east_ready_o)
    // - South
    , .south_data_i (ib_south_data_i )
    , .south_valid_i(ib_south_valid_i)
    , .south_ready_o(ib_south_ready_o)
    // - West
    , .west_data_i (ib_west_data_i )
    , .west_valid_i(ib_west_valid_i)
    , .west_ready_o(ib_west_ready_o)
    // Outbound stream for this node
    , .internal_data_o (dcd_data )
    , .internal_valid_o(dcd_valid)
    , .internal_ready_i(dcd_ready)
    // Outbound stream for bypass
    , .bypass_data_o (byp_data )
    , .bypass_dir_o  (byp_dir  )
    , .bypass_valid_o(byp_valid)
    , .bypass_ready_i(byp_ready)
);

// -----------------------------------------------------------------------------
// Distributor
// -----------------------------------------------------------------------------

nx_message_t   outbound_data;
nx_direction_t outbound_dir;
logic          outbound_valid, outbound_ready;

nx_stream_distributor outbound_dist (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Idle flag
    , .idle_o(dist_idle)
    // Inbound message stream
    , .dist_data_i (outbound_data )
    , .dist_dir_i  (outbound_dir  )
    , .dist_valid_i(outbound_valid)
    , .dist_ready_o(outbound_ready)
    // Outbound distributed message streams
    // - North
    , .north_data_o   (ob_north_data_o   )
    , .north_valid_o  (ob_north_valid_o  )
    , .north_ready_i  (ob_north_ready_i  )
    , .north_present_i(ob_north_present_i)
    // - East
    , .east_data_o   (ob_east_data_o   )
    , .east_valid_o  (ob_east_valid_o  )
    , .east_ready_i  (ob_east_ready_i  )
    , .east_present_i(ob_east_present_i)
    // - South
    , .south_data_o   (ob_south_data_o   )
    , .south_valid_o  (ob_south_valid_o  )
    , .south_ready_i  (ob_south_ready_i  )
    , .south_present_i(ob_south_present_i)
    // - West
    , .west_data_o   (ob_west_data_o   )
    , .west_valid_o  (ob_west_valid_o  )
    , .west_ready_i  (ob_west_ready_i  )
    , .west_present_i(ob_west_present_i)
);

// -----------------------------------------------------------------------------
// Decoder
// -----------------------------------------------------------------------------

logic [$clog2(OUTPUTS)-1:0] map_idx;
logic [ ADDR_ROW_WIDTH-1:0] map_tgt_row;
logic [ ADDR_COL_WIDTH-1:0] map_tgt_col;
logic [ $clog2(INPUTS)-1:0] map_tgt_idx;
logic                       map_tgt_seq, map_valid;

logic [$clog2(INPUTS)-1:0] signal_index;
logic                      signal_is_seq, signal_state, signal_valid;

logic [INSTR_WIDTH-1:0] instr_data;
logic                   instr_valid;

nx_msg_decoder #(
      .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .INSTR_WIDTH   (INSTR_WIDTH   )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
) decoder (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Control signals
    , .idle_o(decode_idle)
    // Inbound message stream
    , .msg_data_i (dcd_data )
    , .msg_valid_i(dcd_valid)
    , .msg_ready_o(dcd_ready)
    // I/O mapping handling
    , .map_idx_o    (map_idx    ) // Output to configure
    , .map_tgt_row_o(map_tgt_row) // Target node's row
    , .map_tgt_col_o(map_tgt_col) // Target node's column
    , .map_tgt_idx_o(map_tgt_idx) // Target node's I/O index
    , .map_tgt_seq_o(map_tgt_seq) // Target node's input is sequential
    , .map_valid_o  (map_valid  ) // Mapping is valid
    // Signal state update
    , .signal_index_o (signal_index )
    , .signal_is_seq_o(signal_is_seq)
    , .signal_state_o (signal_state )
    , .signal_valid_o (signal_valid )
    // Instruction load
    , .instr_data_o (instr_data )
    , .instr_valid_o(instr_valid)
);

// -----------------------------------------------------------------------------
// Control
// -----------------------------------------------------------------------------

nx_message_t   emit_data;
nx_direction_t emit_dir;
logic          emit_valid, emit_ready;

logic               core_trigger;
logic [ INPUTS-1:0] core_inputs;
logic [OUTPUTS-1:0] core_outputs;

logic [$clog2(OP_STORE_LENGTH)-1:0] ctrl_addr;
logic [         OP_STORE_WIDTH-1:0] ctrl_wr_data, ctrl_rd_data;
logic                               ctrl_wr_en, ctrl_rd_en;

nx_node_control #(
      .ADDR_ROW_WIDTH (ADDR_ROW_WIDTH )
    , .ADDR_COL_WIDTH (ADDR_COL_WIDTH )
    , .INPUTS         (INPUTS         )
    , .OUTPUTS        (OUTPUTS        )
    , .OP_STORE_LENGTH(OP_STORE_LENGTH)
    , .OP_STORE_WIDTH (OP_STORE_WIDTH )
) control (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Control signals
    , .idle_o    (ctrl_idle )
    , .node_row_i(node_row_i)
    , .node_col_i(node_col_i)
    // External trigger signal
    , .trigger_i(trigger_i)
    // Channel tokens
    , .token_grant_i  (token_grant_i  )
    , .token_release_o(token_release_o)
    // Outbound message stream
    , .msg_data_o (emit_data )
    , .msg_dir_o  (emit_dir  )
    , .msg_valid_o(emit_valid)
    , .msg_ready_i(emit_ready)
    // I/O mapping
    , .map_idx_i    (map_idx    )
    , .map_tgt_row_i(map_tgt_row)
    , .map_tgt_col_i(map_tgt_col)
    , .map_tgt_idx_i(map_tgt_idx)
    , .map_tgt_seq_i(map_tgt_seq)
    , .map_valid_i  (map_valid  )
    // Signal state update
    , .signal_index_i (signal_index )
    , .signal_is_seq_i(signal_is_seq)
    , .signal_state_i (signal_state )
    , .signal_valid_i (signal_valid )
    // Interface to core
    , .core_trigger_o(core_trigger)
    , .core_inputs_o (core_inputs )
    , .core_outputs_i(core_outputs)
    // Interface to memory
    , .store_addr_o   (ctrl_addr   )
    , .store_wr_data_o(ctrl_wr_data)
    , .store_wr_en_o  (ctrl_wr_en  )
    , .store_rd_en_o  (ctrl_rd_en  )
    , .store_rd_data_i(ctrl_rd_data)
);

// -----------------------------------------------------------------------------
// Combiner
// -----------------------------------------------------------------------------

nx_stream_combiner #(
    .ARB_SCHEME  ("prefer_a"  )
) combiner (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Inbound message streams
    // - A
    , .stream_a_data_i (byp_data )
    , .stream_a_dir_i  (byp_dir  )
    , .stream_a_valid_i(byp_valid)
    , .stream_a_ready_o(byp_ready)
    // - B
    , .stream_b_data_i (emit_data )
    , .stream_b_dir_i  (emit_dir  )
    , .stream_b_valid_i(emit_valid)
    , .stream_b_ready_o(emit_ready)
    // Outbound arbitrated message stream
    , .comb_data_o (outbound_data )
    , .comb_dir_o  (outbound_dir  )
    , .comb_valid_o(outbound_valid)
    , .comb_ready_i(outbound_ready)
);

// -----------------------------------------------------------------------------
// Instruction Store
// -----------------------------------------------------------------------------

logic [$clog2(MAX_INSTRS)-1:0] core_populated;

logic [$clog2(MAX_INSTRS)-1:0] core_addr;
logic [       INSTR_WIDTH-1:0] core_data;
logic                          core_rd, core_stall;

nx_node_store #(
      .INSTR_WIDTH(INSTR_WIDTH    )
    , .MAX_INSTRS (MAX_INSTRS     )
    , .CTRL_WIDTH (OP_STORE_WIDTH )
    , .MAX_CTRL   (OP_STORE_LENGTH)
) store (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Populated instruction counter
    , .instr_count_o(core_populated)
    // Instruction load interface
    , .store_data_i (instr_data )
    , .store_valid_i(instr_valid)
    // Instruction fetch interfaces
    , .fetch_addr_i (core_addr )
    , .fetch_rd_i   (core_rd   )
    , .fetch_data_o (core_data )
    , .fetch_stall_o(core_stall)
    // Control block interface
    , .ctrl_addr_i   (ctrl_addr   )
    , .ctrl_wr_data_i(ctrl_wr_data)
    , .ctrl_wr_en_i  (ctrl_wr_en  )
    , .ctrl_rd_en_i  (ctrl_rd_en  )
    , .ctrl_rd_data_o(ctrl_rd_data)
);

// -----------------------------------------------------------------------------
// Logic Core
// -----------------------------------------------------------------------------

nx_node_core #(
      .INPUTS      (INPUTS      )
    , .OUTPUTS     (OUTPUTS     )
    , .REGISTERS   (REGISTERS   )
    , .MAX_INSTRS  (MAX_INSTRS  )
    , .INSTR_WIDTH (INSTR_WIDTH )
    , .OPCODE_WIDTH(OPCODE_WIDTH)
) core (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // I/O from simulated logic
    , .inputs_i (core_inputs )
    , .outputs_o(core_outputs)
    // Execution controls
    , .populated_i(core_populated)
    , .trigger_i  (core_trigger  )
    , .idle_o     (core_idle     )
    // Instruction fetch
    , .instr_addr_o (core_addr )
    , .instr_rd_o   (core_rd   )
    , .instr_data_i (core_data )
    , .instr_stall_i(core_stall)
);

endmodule : nx_node
