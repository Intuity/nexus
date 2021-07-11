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
      parameter STREAM_WIDTH    =  32
    , parameter ADDR_ROW_WIDTH  =   4
    , parameter ADDR_COL_WIDTH  =   4
    , parameter COMMAND_WIDTH   =   2
    , parameter INSTR_WIDTH     =  15
    , parameter INPUTS          =   8
    , parameter OUTPUTS         =   8
    , parameter REGISTERS       =   8
    , parameter MAX_INSTRS      = 512
    , parameter OPCODE_WIDTH    =   3
    , parameter OP_STORE_LENGTH = 512
    , parameter OP_STORE_WIDTH  = ADDR_ROW_WIDTH + ADDR_COL_WIDTH + $clog2(INPUTS) + 1
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
    , input  logic [STREAM_WIDTH-1:0] ib_north_data_i
    , input  logic                    ib_north_valid_i
    , output logic                    ib_north_ready_o
    // - East
    , input  logic [STREAM_WIDTH-1:0] ib_east_data_i
    , input  logic                    ib_east_valid_i
    , output logic                    ib_east_ready_o
    // - South
    , input  logic [STREAM_WIDTH-1:0] ib_south_data_i
    , input  logic                    ib_south_valid_i
    , output logic                    ib_south_ready_o
    // - West
    , input  logic [STREAM_WIDTH-1:0] ib_west_data_i
    , input  logic                    ib_west_valid_i
    , output logic                    ib_west_ready_o
    // Outbound interfaces
    // - North
    , output logic [STREAM_WIDTH-1:0] ob_north_data_o
    , output logic                    ob_north_valid_o
    , input  logic                    ob_north_ready_i
    , input  logic                    ob_north_present_i
    // - East
    , output logic [STREAM_WIDTH-1:0] ob_east_data_o
    , output logic                    ob_east_valid_o
    , input  logic                    ob_east_ready_i
    , input  logic                    ob_east_present_i
    // - South
    , output logic [STREAM_WIDTH-1:0] ob_south_data_o
    , output logic                    ob_south_valid_o
    , input  logic                    ob_south_ready_i
    , input  logic                    ob_south_present_i
    // - West
    , output logic [STREAM_WIDTH-1:0] ob_west_data_o
    , output logic                    ob_west_valid_o
    , input  logic                    ob_west_ready_i
    , input  logic                    ob_west_present_i
);

// -----------------------------------------------------------------------------
// Idle Control
// -----------------------------------------------------------------------------

`DECLARE_DQ(1, idle, clk_i, rst_i, 1'b0)

assign idle = (
    core_idle && decode_idle && !inbound_valid && !outbound_valid && ctrl_idle
);

assign idle_o = idle_q;

// -----------------------------------------------------------------------------
// Arbiter
// -----------------------------------------------------------------------------

logic [STREAM_WIDTH-1:0] inbound_data;
logic [             1:0] inbound_dir;
logic                    inbound_valid, inbound_ready;

nx_stream_arbiter #(
      .STREAM_WIDTH(STREAM_WIDTH)
    , .SKID_BUFFERS("yes"       )
) inbound_arb (
      .clk_i(clk_i)
    , .rst_i(rst_i)
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
    // Outbound arbitrated message stream
    , .arb_data_o (inbound_data )
    , .arb_dir_o  (inbound_dir  )
    , .arb_valid_o(inbound_valid)
    , .arb_ready_i(inbound_ready)
);

localparam MAX_IO = ((INPUTS > OUTPUTS) ? INPUTS : OUTPUTS);

// -----------------------------------------------------------------------------
// Distributor
// -----------------------------------------------------------------------------

logic [STREAM_WIDTH-1:0] outbound_data;
logic [             1:0] outbound_dir;
logic                    outbound_valid, outbound_ready;

nx_stream_distributor #(
      .STREAM_WIDTH(STREAM_WIDTH)
    , .SKID_BUFFERS("no"        )
) outbound_dist (
      .clk_i(clk_i)
    , .rst_i(rst_i)
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

logic decode_idle;

logic [STREAM_WIDTH-1:0] bypass_data;
logic [             1:0] bypass_dir;
logic                    bypass_valid, bypass_ready;

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
      .STREAM_WIDTH  (STREAM_WIDTH  )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
    , .INSTR_WIDTH   (INSTR_WIDTH   )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
) decoder (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Control signals
    , .idle_o    (decode_idle)
    , .node_row_i(node_row_i )
    , .node_col_i(node_col_i )
    // Inbound message stream
    , .msg_data_i (inbound_data )
    , .msg_dir_i  (inbound_dir  )
    , .msg_valid_i(inbound_valid)
    , .msg_ready_o(inbound_ready)
    // Outbound bypass message stream
    , .bypass_data_o (bypass_data )
    , .bypass_dir_o  (bypass_dir  )
    , .bypass_valid_o(bypass_valid)
    , .bypass_ready_i(bypass_ready)
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

logic ctrl_idle;

logic [STREAM_WIDTH-1:0] emit_data;
logic [             1:0] emit_dir;
logic                    emit_valid, emit_ready;

logic               core_trigger;
logic [ INPUTS-1:0] core_inputs;
logic [OUTPUTS-1:0] core_outputs;

logic [$clog2(OP_STORE_LENGTH)-1:0] ctrl_addr;
logic [         OP_STORE_WIDTH-1:0] ctrl_wr_data, ctrl_rd_data;
logic                               ctrl_wr_en, ctrl_rd_en;

nx_node_control #(
      .STREAM_WIDTH   (STREAM_WIDTH   )
    , .ADDR_ROW_WIDTH (ADDR_ROW_WIDTH )
    , .ADDR_COL_WIDTH (ADDR_COL_WIDTH )
    , .COMMAND_WIDTH  (COMMAND_WIDTH  )
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
      .STREAM_WIDTH(STREAM_WIDTH)
    , .ARB_SCHEME  ("prefer_a"  )
) combiner (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Inbound message streams
    // - A
    , .stream_a_data_i (bypass_data )
    , .stream_a_dir_i  (bypass_dir  )
    , .stream_a_valid_i(bypass_valid)
    , .stream_a_ready_o(bypass_ready)
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

logic core_idle;

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
