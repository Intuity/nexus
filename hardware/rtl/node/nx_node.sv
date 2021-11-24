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
module nx_node
import NXConstants::*,
       nx_primitives::ROUND_ROBIN,
       nx_primitives::ORDINAL;
#(
      parameter INPUTS     = 32
    , parameter OUTPUTS    = 32
    , parameter REGISTERS  = 16
    , parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic                          i_clk
    , input  logic                          i_rst
    // Control signals
    , input  node_id_t                      i_node_id
    , input  logic                          i_idle
    , output logic                          o_idle
    , input  logic                          i_trigger
    , output logic                          o_trigger
    // Inbound interfaces
    , input  logic [3:0][MESSAGE_WIDTH-1:0] i_inbound_data
    , input  logic [3:0]                    i_inbound_valid
    , output logic [3:0]                    o_inbound_ready
    // Outbound interfaces
    , output logic [3:0][MESSAGE_WIDTH-1:0] o_outbound_data
    , output logic [3:0]                    o_outbound_valid
    , input  logic [3:0]                    i_outbound_ready
    , input  logic [3:0]                    i_outbound_present
);

// =============================================================================
// Signals & State
// =============================================================================

// Idle and trigger signal chaining
`DECLARE_DQ(1, idle,    i_clk, i_rst, 'd0)
`DECLARE_DQ(1, trigger, i_clk, i_rst, 'd0)

// Idle control
struct packed { logic core, decode, ctrl, distrib; } comp_idle;

// Inbound stream arbiter
node_message_t arb_data;
logic          arb_valid, arb_ready, arb_match;

// Stream combiner
// NOTE: Not using node_message_t is a workaround for Icarus Verilog
logic [1:0][MESSAGE_WIDTH-1:0] comb_data;
logic [1:0]                    comb_valid, comb_ready;

// Outbound stream distributor
node_message_t outbound_data;
logic          outbound_valid, outbound_ready;
direction_t    outbound_dir;

// Message decoder
logic                        dcd_valid, dcd_ready;
logic [RAM_ADDR_W-1:0]       dcd_wr_addr;
logic [RAM_DATA_W-1:0]       dcd_wr_data;
logic                        dcd_wr_en;
logic [INPUTS-1:0]           dcd_loopback_mask;
logic [$clog2(INPUTS)-1:0]   dcd_input_index;
logic                        dcd_input_value, dcd_input_is_seq, dcd_input_update;
logic [NODE_PARAM_WIDTH-1:0] dcd_num_instr;

// Controller
logic [RAM_ADDR_W-1:0] ctrl_rd_addr;
logic [RAM_DATA_W-1:0] ctrl_rd_data;
logic                  ctrl_rd_en;

// Logic core
logic [INPUTS-1:0]     core_inputs;
logic [OUTPUTS-1:0]    core_outputs;
logic                  core_trigger;
logic [RAM_ADDR_W-1:0] core_rd_addr;
logic [RAM_DATA_W-1:0] core_rd_data;
logic                  core_rd_en, core_rd_stall;

// =============================================================================
// Trigger and Idle Chaining
// =============================================================================

// Determine local idleness
assign idle = (&comp_idle) && !dcd_valid && !(|comb_valid);

// Chain idle signal through the node
assign o_idle = idle_q && i_idle;

// Chain trigger signal
assign trigger   = i_trigger;
assign o_trigger = trigger_q;

// =============================================================================
// Inbound Stream Arbiter
// =============================================================================

nx_stream_arbiter #(
      .STREAMS          ( 4               )
    , .SCHEME           ( ROUND_ROBIN     )
) u_arbiter (
      .i_clk            ( i_clk           )
    , .i_rst            ( i_rst           )
    // Inbound message streams
    , .i_inbound_data   ( i_inbound_data  )
    , .i_inbound_valid  ( i_inbound_valid )
    , .o_inbound_ready  ( o_inbound_ready )
    // Outbound stream
    , .o_outbound_data  ( arb_data        )
    , .o_outbound_valid ( arb_valid       )
    , .i_outbound_ready ( arb_ready       )
);

// Link arbitrated data up to the combiner's bypass port
assign comb_data[0] = arb_data;

// Detect if the arbitrated stream targets this node
assign arb_match = (
    (arb_data.raw.header.row    == i_node_id.row   ) &&
    (arb_data.raw.header.column == i_node_id.column)
);

// Discern decode from bypass traffic
assign dcd_valid     = arb_valid &&  arb_match;
assign comb_valid[0] = arb_valid && !arb_match;

// Qualify the ready signal
assign arb_ready = (dcd_ready && arb_match) || (comb_ready[0] && !arb_match);

// =============================================================================
// Internal Stream Combiner
// =============================================================================

nx_stream_arbiter #(
      .STREAMS          ( 2              )
    , .SCHEME           ( ORDINAL        )
) u_combiner (
      .i_clk            ( i_clk          )
    , .i_rst            ( i_rst          )
    // Inbound message streams
    , .i_inbound_data   ( comb_data      )
    , .i_inbound_valid  ( comb_valid     )
    , .o_inbound_ready  ( comb_ready     )
    // Outbound stream
    , .o_outbound_data  ( outbound_data  )
    , .o_outbound_valid ( outbound_valid )
    , .i_outbound_ready ( outbound_ready )
);

// =============================================================================
// Distributor
// =============================================================================

// Determine target direction based on two factors:
//  - Target row & column set the initial direction
//  - If a particular direction is absent, routes to the next clockwise stream
always_comb begin : comb_outbound_dir
    logic lt_row, gt_row, lt_col, gt_col;
    lt_row = (outbound_data.raw.header.row    < i_node_id.row   );
    gt_row = (outbound_data.raw.header.row    > i_node_id.row   );
    lt_col = (outbound_data.raw.header.column < i_node_id.column);
    gt_col = (outbound_data.raw.header.column > i_node_id.column);
    casez ({ lt_row, gt_row, lt_col, gt_col, i_outbound_present })
    //     <R    >R    <C    >C   PRSNT
        { 1'b1, 1'b0, 1'b?, 1'b?, 4'b???1 }: outbound_dir = DIRECTION_NORTH;
        { 1'b1, 1'b0, 1'b?, 1'b?, 4'b???0 }: outbound_dir = DIRECTION_EAST;
        { 1'b0, 1'b1, 1'b?, 1'b?, 4'b?1?? }: outbound_dir = DIRECTION_SOUTH;
        { 1'b0, 1'b1, 1'b?, 1'b?, 4'b?0?? }: outbound_dir = DIRECTION_WEST;
        { 1'b0, 1'b0, 1'b1, 1'b0, 4'b1??? }: outbound_dir = DIRECTION_WEST;
        { 1'b0, 1'b0, 1'b1, 1'b0, 4'b0??? }: outbound_dir = DIRECTION_NORTH;
        { 1'b0, 1'b0, 1'b0, 1'b1, 4'b??1? }: outbound_dir = DIRECTION_EAST;
        { 1'b0, 1'b0, 1'b0, 1'b1, 4'b??0? }: outbound_dir = DIRECTION_SOUTH;
        default: outbound_dir = DIRECTION_NORTH;
    endcase
end

nx_stream_distributor #(
      .STREAMS          ( 4                 )
) u_distributor (
      .i_clk            ( i_clk             )
    , .i_rst            ( i_rst             )
    // Idle flag
    , .o_idle           ( comp_idle.distrib )
    // Inbound message stream
    , .i_inbound_dir    ( outbound_dir      )
    , .i_inbound_data   ( outbound_data     )
    , .i_inbound_valid  ( outbound_valid    )
    , .o_inbound_ready  ( outbound_ready    )
    // Outbound message streams
    , .o_outbound_data  ( o_outbound_data   )
    , .o_outbound_valid ( o_outbound_valid  )
    , .i_outbound_ready ( i_outbound_ready  )
);

// =============================================================================
// Decoder
// =============================================================================

nx_node_decoder #(
      .INPUTS          ( INPUTS            )
    , .RAM_ADDR_W      ( RAM_ADDR_W        )
    , .RAM_DATA_W      ( RAM_DATA_W        )
) u_decoder (
      .i_clk           ( i_clk             )
    , .i_rst           ( i_rst             )
    // Control signals
    , .o_idle          ( comp_idle.decode  )
    // Inbound message stream
    , .i_msg_data      ( comb_data[0]      )
    , .i_msg_valid     ( dcd_valid         )
    , .o_msg_ready     ( dcd_ready         )
    // Write interface to node's memory (driven by node_load_t)
    , .o_ram_addr      ( dcd_wr_addr       )
    , .o_ram_wr_data   ( dcd_wr_data       )
    , .o_ram_wr_en     ( dcd_wr_en         )
    // Input signal state (driven by node_signal_t)
    , .o_input_index   ( dcd_input_index   )
    , .o_input_value   ( dcd_input_value   )
    , .o_input_is_seq  ( dcd_input_is_seq  )
    , .o_input_update  ( dcd_input_update  )
    // Control parameters (driven by node_control_t)
    , .o_num_instr     ( dcd_num_instr     )
    , .o_loopback_mask ( dcd_loopback_mask )
);

// =============================================================================
// Control
// =============================================================================

nx_node_control #(
      .INPUTS          ( INPUTS            )
    , .OUTPUTS         ( OUTPUTS           )
    , .RAM_ADDR_W      ( RAM_ADDR_W        )
    , .RAM_DATA_W      ( RAM_DATA_W        )
) u_control (
      .i_clk           ( i_clk             )
    , .i_rst           ( i_rst             )
    // Control signals
    , .i_trigger       ( i_trigger         )
    , .o_idle          ( comp_idle.ctrl    )
    // Inputs from decoder
    , .i_loopback_mask ( dcd_loopback_mask )
    , .i_input_index   ( dcd_input_index   )
    , .i_input_value   ( dcd_input_value   )
    , .i_input_is_seq  ( dcd_input_is_seq  )
    , .i_input_update  ( dcd_input_update  )
    , .i_num_instr     ( dcd_num_instr     )
    // Output message stream
    , .o_msg_data      ( comb_data[1]      )
    , .o_msg_valid     ( comb_valid[1]     )
    , .i_msg_ready     ( comb_ready[1]     )
    // Interface to store
    , .o_ram_addr      ( ctrl_rd_addr      )
    , .o_ram_rd_en     ( ctrl_rd_en        )
    , .i_ram_rd_data   ( ctrl_rd_data      )
    // Interface to logic core
    , .o_core_inputs   ( core_inputs       )
    , .i_core_outputs  ( core_outputs      )
    , .o_core_trigger  ( core_trigger      )
);

// =============================================================================
// Data Store
// =============================================================================

nx_node_store #(
      .RAM_ADDR_W    ( RAM_ADDR_W    )
    , .RAM_DATA_W    ( RAM_DATA_W    )
    , .REGISTER_A_RD ( 1             )
    , .REGISTER_B_RD ( 0             )
) u_store (
      .i_clk         ( i_clk         )
    , .i_rst         ( i_rst         )
    // Write port
    , .i_wr_addr     ( dcd_wr_addr   )
    , .i_wr_data     ( dcd_wr_data   )
    , .i_wr_en       ( dcd_wr_en     )
    // Read ports
    // - A
    , .i_a_rd_addr   ( core_rd_addr  )
    , .i_a_rd_en     ( core_rd_en    )
    , .o_a_rd_data   ( core_rd_data  )
    , .o_a_rd_stall  ( core_rd_stall )
    // - B
    , .i_b_rd_addr   ( ctrl_rd_addr  )
    , .i_b_rd_en     ( ctrl_rd_en    )
    , .o_b_rd_data   ( ctrl_rd_data  )
);

// =============================================================================
// Logic Core
// =============================================================================

nx_node_core #(
      .INPUTS          ( INPUTS         )
    , .OUTPUTS         ( OUTPUTS        )
    , .REGISTERS       ( REGISTERS      )
) u_core (
      .i_clk           ( i_clk          )
    , .i_rst           ( i_rst          )
    // I/O from simulated logic
    , .i_inputs        ( core_inputs    )
    , .o_outputs       ( core_outputs   )
    // Execution controls
    , .i_populated     ( dcd_num_instr  )
    , .i_trigger       ( core_trigger   )
    , .o_idle          ( comp_idle.core )
    // Instruction fetch
    , .o_instr_addr    ( core_rd_addr   )
    , .o_instr_rd_en   ( core_rd_en     )
    , .i_instr_rd_data ( core_rd_data   )
    , .i_instr_stall   ( core_rd_stall  )
);

endmodule : nx_node
