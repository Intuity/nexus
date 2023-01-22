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
// Execution core of each node that evaluates the instruction sequence
//
module nx_node_core
import NXConstants::*;
#(
      localparam RAM_ADDR_W = 10
    , localparam RAM_DATA_W = 32
    , localparam RAM_STRB_W =  4
) (
      input  logic                  i_clk
    , input  logic                  i_rst
    // Control signals
    , output logic                  o_idle
    , input  logic                  i_trigger
    // Instruction RAM
    , output logic [RAM_ADDR_W-1:0] o_inst_addr
    , output logic                  o_inst_rd_en
    , input  logic [RAM_DATA_W-1:0] i_inst_rd_data
    // Data RAM
    , output logic [RAM_ADDR_W-1:0] o_data_addr
    , output logic [RAM_DATA_W-1:0] o_data_wr_data
    , output logic [RAM_STRB_W-1:0] o_data_wr_strb
    , output logic                  o_data_rd_en
    , input  logic [RAM_DATA_W-1:0] i_data_rd_data
    // Outbound messages
    , input  node_message_t         o_send_data
    , input  logic                  o_send_valid
    , output logic                  i_send_ready
);

endmodule : nx_node_core
