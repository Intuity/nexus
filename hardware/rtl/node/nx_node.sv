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

// nx_node
// A single node with messages interfaces in each cardinal direction
//
module nx_node
import NXConstants::*,
       nx_primitives::ORDINAL;
(
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

localparam RAM_ADDR_W = 10;
localparam RAM_DATA_W = 32;

// =============================================================================
// Signals
// =============================================================================

// Instruction and data RAMs
logic [RAM_ADDR_W-1:0] inst_addr_a, inst_addr_b, data_addr_a, data_addr_b;
logic [RAM_DATA_W-1:0] inst_wr_data_a, inst_rd_data_b,
                       data_wr_data_a, data_wr_data_b, data_rd_data_b;
logic [RAM_DATA_W-1:0] inst_wr_strb_a, data_wr_strb_a, data_wr_strb_b;
logic                  inst_rd_en_b, data_rd_en_b;

// Stream combiner
// NOTE: Not using node_message_t is a workaround for Icarus Verilog
logic [1:0][MESSAGE_WIDTH-1:0] comb_data;
logic [1:0]                    comb_valid, comb_ready;

// Outbound stream distributor
node_message_t outbound_data;
logic          outbound_valid, outbound_ready;

// Idle signals
logic decd_idle, dist_idle, core_idle;

// Slot
logic slot;

// =============================================================================
// Instruction RAM
// =============================================================================

nx_ram #(
      .ADDRESS_WIDTH ( RAM_ADDR_W )
    , .DATA_WIDTH    ( RAM_DATA_W )
    , .BIT_WR_EN_A   ( 1          )
    , .BIT_WR_EN_B   ( 1          )
    , .REGISTER_A_RD ( 1          )
    , .REGISTER_B_RD ( 1          )
) u_inst_ram (
      .i_clk_a     ( i_clk             )
    , .i_rst_a     ( i_rst             )
    , .i_addr_a    ( inst_addr_a       )
    , .i_wr_data_a ( inst_wr_data_a    )
    , .i_wr_en_a   ( inst_wr_strb_a    )
    , .i_en_a      ( (|inst_wr_strb_a) )
    , .o_rd_data_a (                   )
    , .i_clk_b     ( i_clk             )
    , .i_rst_b     ( i_rst             )
    , .i_addr_b    ( inst_addr_b       )
    , .i_wr_data_b ( RAM_DATA_W'(0)    )
    , .i_wr_en_b   ( RAM_DATA_W'(0)    )
    , .i_en_b      ( inst_rd_en_b      )
    , .o_rd_data_b ( inst_rd_data_b    )
);

// =============================================================================
// Data RAM
// =============================================================================

nx_ram #(
      .ADDRESS_WIDTH ( RAM_ADDR_W )
    , .DATA_WIDTH    ( RAM_DATA_W )
    , .BIT_WR_EN_A   ( 1          )
    , .BIT_WR_EN_B   ( 1          )
    , .REGISTER_A_RD ( 1          )
    , .REGISTER_B_RD ( 1          )
) u_data_ram (
      .i_clk_a     ( i_clk                             )
    , .i_rst_a     ( i_rst                             )
    , .i_addr_a    ( data_addr_a                       )
    , .i_wr_data_a ( data_wr_data_a                    )
    , .i_wr_en_a   ( data_wr_strb_a                    )
    , .i_en_a      ( (|data_wr_strb_a)                 )
    , .o_rd_data_a (                                   )
    , .i_clk_b     ( i_clk                             )
    , .i_rst_b     ( i_rst                             )
    , .i_addr_b    ( data_addr_b                       )
    , .i_wr_data_b ( data_wr_data_b                    )
    , .i_wr_en_b   ( data_wr_strb_b                    )
    , .i_en_b      ( (|data_wr_strb_b) || data_rd_en_b )
    , .o_rd_data_b ( data_rd_data_b                    )
);

// =============================================================================
// Messaging
// =============================================================================

nx_node_decoder u_decoder (
      .i_clk           ( i_clk           )
    , .i_rst           ( i_rst           )
    // Control signals
    , .i_node_id       ( i_node_id       )
    , .o_idle          ( decd_idle       )
    , .i_slot          ( slot            )
    // Inbound interfaces
    , .i_inbound_data  ( i_inbound_data  )
    , .i_inbound_valid ( i_inbound_valid )
    , .o_inbound_ready ( o_inbound_ready )
    // Bypass interface
    , .o_bypass_data   ( comb_data[0]    )
    , .o_bypass_valid  ( comb_valid[0]   )
    , .i_bypass_ready  ( comb_ready[0]   )
    // Instruction RAM
    , .o_inst_addr     ( inst_addr_a     )
    , .o_inst_wr_data  ( inst_wr_data_a  )
    , .o_inst_wr_strb  ( inst_wr_strb_a  )
    // Data RAM
    , .o_data_addr     ( data_addr_a     )
    , .o_data_wr_data  ( data_wr_data_a  )
    , .o_data_wr_strb  ( data_wr_strb_a  )
);

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

nx_node_distributor u_distributor (
      .i_clk              ( i_clk              )
    , .i_rst              ( i_rst              )
    // Control signals
    , .i_node_id          ( i_node_id          )
    , .o_idle             ( dist_idle          )
    // Message to send
    , .i_outbound_data    ( outbound_data      )
    , .i_outbound_valid   ( outbound_valid     )
    , .o_outbound_ready   ( outbound_ready     )
    // Outbound interfaces
    , .o_external_data    ( o_outbound_data    )
    , .o_external_valid   ( o_outbound_valid   )
    , .i_external_ready   ( i_outbound_ready   )
    , .i_external_present ( i_outbound_present )
);

// =============================================================================
// Execution Core
// =============================================================================

nx_node_core u_core (
      .i_clk          ( i_clk          )
    , .i_rst          ( i_rst          )
    // Control signals
    , .o_idle         ( core_idle      )
    , .i_trigger      ( i_trigger      )
    , .o_slot         ( slot           )
    // Instruction RAM
    , .o_inst_addr    ( inst_addr_b    )
    , .o_inst_rd_en   ( inst_rd_en_b   )
    , .i_inst_rd_data ( inst_rd_data_b )
    // Data RAM
    , .o_data_addr    ( data_addr_b    )
    , .o_data_wr_data ( data_wr_data_b )
    , .o_data_wr_strb ( data_wr_strb_b )
    , .o_data_rd_en   ( data_rd_en_b   )
    , .i_data_rd_data ( data_rd_data_b )
    // Outbound messages
    , .o_send_data    ( comb_data[1]   )
    , .o_send_valid   ( comb_valid[1]  )
    , .i_send_ready   ( comb_ready[1]  )
);

// =============================================================================
// Idle & Trigger
// =============================================================================

assign o_idle    = &{i_idle, decd_idle, dist_idle, core_idle};
assign o_trigger = i_trigger;

endmodule : nx_node
