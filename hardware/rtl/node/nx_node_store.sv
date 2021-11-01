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

// nx_node_store
// The node's internal memory with three access ports - a write port used by the
// decoder to load data into the memory, a read port used by the core to fetch
// instructions, and a second read port used by the control block to generate
// output messages. The decoder write port and core read port are arbitrated
// onto the same physical port of a dual-ported RAM.
//
module nx_node_store
import NXConstants::*;
#(
      parameter RAM_ADDR_W = 10
    , parameter RAM_DATA_W = 32
) (
      input  logic                  i_clk
    , input  logic                  i_rst
    // Write port
    , input  logic [RAM_ADDR_W-1:0] i_wr_addr
    , input  logic [RAM_DATA_W-1:0] i_wr_data
    , input  logic                  i_wr_en
    // Read ports
    // - A
    , input  logic [RAM_ADDR_W-1:0] i_a_rd_addr
    , input  logic                  i_a_rd_en
    , output logic [RAM_DATA_W-1:0] o_a_rd_data
    , output logic                  o_a_rd_stall
    // - B
    , input  logic [RAM_ADDR_W-1:0] i_b_rd_addr
    , input  logic                  i_b_rd_en
    , output logic [RAM_DATA_W-1:0] o_b_rd_data
);

// Mux port A between the write stream and read port A
logic [RAM_ADDR_W-1:0] muxed_addr;
logic                  muxed_en;

assign muxed_addr   = i_wr_en ? i_wr_addr : i_a_rd_addr;
assign muxed_en     = i_wr_en || i_a_rd_en;
assign o_a_rd_stall = i_wr_en;

// Instance the RAM
nx_ram #(
      .ADDRESS_WIDTH ( RAM_ADDR_W )
    , .DATA_WIDTH    ( RAM_DATA_W )
) u_ram (
    // Port A
      .i_clk_a     ( i_clk       )
    , .i_rst_a     ( i_rst       )
    , .i_addr_a    ( muxed_addr  )
    , .i_wr_data_a ( i_wr_data   )
    , .i_wr_en_a   ( i_wr_en     )
    , .i_en_a      ( muxed_en    )
    , .o_rd_data_a ( o_a_rd_data )
    // Port B
    , .i_clk_b     ( i_clk       )
    , .i_rst_b     ( i_rst       )
    , .i_addr_b    ( i_b_rd_addr )
    , .i_wr_data_b ( 'd0         )
    , .i_wr_en_b   ( 'd0         )
    , .i_en_b      ( i_b_rd_en   )
    , .o_rd_data_b ( o_b_rd_data )
);

endmodule : nx_node_store
