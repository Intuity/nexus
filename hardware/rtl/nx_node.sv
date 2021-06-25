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
      parameter STREAM_WIDTH   =  32
    , parameter ADDR_ROW_WIDTH =   4
    , parameter ADDR_COL_WIDTH =   4
    , parameter COMMAND_WIDTH  =   2
    , parameter INSTR_WIDTH    =  15
    , parameter INPUTS         =   8
    , parameter OUTPUTS        =   8
    , parameter REGISTERS      =   8
    , parameter MAX_INSTRS     = 512
    , parameter OPCODE_WIDTH   =   3
) (
      input  logic clk_i
    , input  logic rst_i
    // Control signals
    , input  logic trigger_i
    , output logic idle_o
    , input  logic [ADDR_ROW_WIDTH-1:0] node_row_i
    , input  logic [ADDR_COL_WIDTH-1:0] node_col_i
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

assign idle_o = core_idle[0] && core_idle[1] && !inbound_valid && !outbound_valid;

// -----------------------------------------------------------------------------
// Arbiter
// -----------------------------------------------------------------------------

logic [STREAM_WIDTH-1:0] inbound_data;
logic [             1:0] inbound_dir;
logic                    inbound_valid, inbound_ready;

nx_stream_arbiter #(
    .STREAM_WIDTH(STREAM_WIDTH)
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

logic [STREAM_WIDTH-1:0] bypass_data;
logic [             1:0] bypass_dir;
logic                    bypass_valid, bypass_ready;

logic [ $clog2(MAX_IO)-1:0] map_io;
logic [ ADDR_ROW_WIDTH-1:0] map_remote_row;
logic [ ADDR_COL_WIDTH-1:0] map_remote_col;
logic [$clog2(OUTPUTS)-1:0] map_remote_idx;
logic                       map_input, map_slot, map_broadcast, map_seq, map_valid;

logic [ ADDR_ROW_WIDTH-1:0] signal_remote_row;
logic [ ADDR_COL_WIDTH-1:0] signal_remote_col;
logic [$clog2(OUTPUTS)-1:0] signal_remote_idx;
logic                       signal_state, signal_valid;

logic [INSTR_WIDTH-1:0] instr_data;
logic                   instr_core, instr_valid;

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
    // Node identity
    , .node_row_i(node_row_i)
    , .node_col_i(node_col_i)
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
    , .map_io_o        (map_io        )
    , .map_input_o     (map_input     )
    , .map_remote_row_o(map_remote_row)
    , .map_remote_col_o(map_remote_col)
    , .map_remote_idx_o(map_remote_idx)
    , .map_slot_o      (map_slot      )
    , .map_broadcast_o (map_broadcast )
    , .map_seq_o       (map_seq       )
    , .map_valid_o     (map_valid     )
    // Signal state update
    , .signal_remote_row_o(signal_remote_row)
    , .signal_remote_col_o(signal_remote_col)
    , .signal_remote_idx_o(signal_remote_idx)
    , .signal_state_o     (signal_state     )
    , .signal_valid_o     (signal_valid     )
    // Instruction load
    , .instr_core_o (instr_core )
    , .instr_data_o (instr_data )
    , .instr_valid_o(instr_valid)
);

// -----------------------------------------------------------------------------
// Control
// -----------------------------------------------------------------------------

logic [STREAM_WIDTH-1:0] emit_data;
logic [             1:0] emit_dir;
logic                    emit_valid, emit_ready;

logic               core_trigger;
logic [ INPUTS-1:0] core_inputs;
logic [OUTPUTS-1:0] core_outputs;

nx_node_control #(
      .STREAM_WIDTH  (STREAM_WIDTH  )
    , .ADDR_ROW_WIDTH(ADDR_ROW_WIDTH)
    , .ADDR_COL_WIDTH(ADDR_COL_WIDTH)
    , .COMMAND_WIDTH (COMMAND_WIDTH )
    , .INPUTS        (INPUTS        )
    , .OUTPUTS       (OUTPUTS       )
) control (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Node identity
    , .node_row_i(node_row_i)
    , .node_col_i(node_col_i)
    // External trigger signal
    , .trigger_i(trigger_i)
    // Outbound message stream
    , .msg_data_o (emit_data )
    , .msg_dir_o  (emit_dir  )
    , .msg_valid_o(emit_valid)
    , .msg_ready_i(emit_ready)
    // I/O mapping
    , .map_io_i        (map_io        )
    , .map_input_i     (map_input     )
    , .map_remote_row_i(map_remote_row)
    , .map_remote_col_i(map_remote_col)
    , .map_remote_idx_i(map_remote_idx)
    , .map_slot_i      (map_slot      )
    , .map_broadcast_i (map_broadcast )
    , .map_seq_i       (map_seq       )
    , .map_valid_i     (map_valid     )
    // Signal state update
    , .signal_remote_row_i(signal_remote_row)
    , .signal_remote_col_i(signal_remote_col)
    , .signal_remote_idx_i(signal_remote_idx)
    , .signal_state_i     (signal_state     )
    , .signal_valid_i     (signal_valid     )
    // Interface to core
    , .core_trigger_o(core_trigger)
    , .core_inputs_o (core_inputs )
    , .core_outputs_i(core_outputs)
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

logic [$clog2(MAX_INSTRS)-1:0] core_populated [1:0];

logic [$clog2(MAX_INSTRS)-1:0] core_addr [1:0];
logic [       INSTR_WIDTH-1:0] core_data [1:0];
logic                          core_rd [1:0], core_stall [1:0];

// TEMP: Tie-off second core as only one core instanced
assign core_addr[1] = 0;
assign core_rd[1]   = 0;

nx_instr_store #(
      .INSTR_WIDTH(INSTR_WIDTH)
    , .MAX_INSTRS (MAX_INSTRS )
) instr_store (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // Instruction load interface
    , .store_core_i (instr_core )
    , .store_data_i (instr_data )
    , .store_valid_i(instr_valid)
    // Populated instruction counters
    , .core_0_populated_o(core_populated[0])
    , .core_1_populated_o(core_populated[1])
    // Instruction fetch interfaces
    // - Core 0
    , .core_0_addr_i (core_addr[0] )
    , .core_0_rd_i   (core_rd[0]   )
    , .core_0_data_o (core_data[0] )
    , .core_0_stall_o(core_stall[0])
    // - Core 1
    , .core_1_addr_i (core_addr[1] )
    , .core_1_rd_i   (core_rd[1]   )
    , .core_1_data_o (core_data[1] )
    , .core_1_stall_o(core_stall[1])
);

// -----------------------------------------------------------------------------
// Logic Core
// -----------------------------------------------------------------------------

logic core_idle [1:0];

assign core_idle[1] = 1'b1;

nx_node_core #(
      .INPUTS      (INPUTS      )
    , .OUTPUTS     (OUTPUTS     )
    , .REGISTERS   (REGISTERS   )
    , .MAX_INSTRS  (MAX_INSTRS  )
    , .INSTR_WIDTH (INSTR_WIDTH )
    , .OPCODE_WIDTH(OPCODE_WIDTH)
) core_0 (
      .clk_i(clk_i)
    , .rst_i(rst_i)
    // I/O from simulated logic
    , .inputs_i (core_inputs )
    , .outputs_o(core_outputs)
    // Execution controls
    , .populated_i(core_populated[0])
    , .trigger_i  (core_trigger     )
    , .idle_o     (core_idle[0]     )
    // Instruction fetch
    , .instr_addr_o (core_addr[0] )
    , .instr_rd_o   (core_rd[0]   )
    , .instr_data_i (core_data[0] )
    , .instr_stall_i(core_stall[0])
);

endmodule : nx_node
