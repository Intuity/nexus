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

// nx_instr_store
// Dual-ported instruction store capable of supporting two independent cores
// within the same node.
//
module nx_instr_store #(
      parameter INSTR_WIDTH =  15 // Width of each instruction
    , parameter MAX_INSTRS  = 512 // Maximum number of instructions per core
) (
      input  logic clk_i
    , input  logic rst_i
    // Instruction load interface
    , input  logic                   store_core_i
    , input  logic [INSTR_WIDTH-1:0] store_data_i
    , input  logic                   store_valid_i
    // Populated instruction counters
    , output logic [$clog2(MAX_INSTRS)-1:0] core_0_populated_o
    , output logic [$clog2(MAX_INSTRS)-1:0] core_1_populated_o
    // Instruction fetch interfaces
    // - Core 0
    , input  logic [$clog2(MAX_INSTRS)-1:0] core_0_addr_i
    , input  logic                          core_0_rd_i
    , output logic [       INSTR_WIDTH-1:0] core_0_data_o
    , output logic                          core_0_stall_o
    // - Core 1
    , input  logic [$clog2(MAX_INSTRS)-1:0] core_1_addr_i
    , input  logic                          core_1_rd_i
    , output logic [       INSTR_WIDTH-1:0] core_1_data_o
    , output logic                          core_1_stall_o
);

// Parameters
localparam INSTR_ADDR_W = $clog2(MAX_INSTRS);

// Internal state
`DECLARE_DQ(INSTR_ADDR_W, populated_0, clk_i, rst_i, {INSTR_ADDR_W{1'b0}})
`DECLARE_DQ(INSTR_ADDR_W, populated_1, clk_i, rst_i, {INSTR_ADDR_W{1'b0}})

// Construct outputs
assign core_0_populated_o = populated_0;
assign core_1_populated_o = populated_1;

assign core_0_stall_o = store_valid_i && !store_core_i;
assign core_1_stall_o = store_valid_i &&  store_core_i;

// Hookup RAM
nx_ram #(
      .ADDRESS_WIDTH(INSTR_ADDR_W + 1)
    , .DATA_WIDTH   (INSTR_WIDTH     )
) ram (
    // Port A
      .clk_a_i    (clk_i)
    , .rst_a_i    (rst_i)
    , .addr_a_i   ({
        1'b0, (store_valid_i && !store_core_i) ? populated_0_q : core_0_addr_i
    })
    , .wr_data_a_i(store_data_i)
    , .wr_en_a_i  (store_valid_i && !store_core_i)
    , .en_a_i     ((store_valid_i && !store_core_i) || core_0_rd_i)
    , .rd_data_a_o(core_0_data_o)
    // Port B
    , .clk_b_i    (clk_i)
    , .rst_b_i    (rst_i)
    , .addr_b_i   ({
        1'b1, (store_valid_i && store_core_i) ? populated_1_q : core_1_addr_i
    })
    , .wr_data_b_i(store_data_i)
    , .wr_en_b_i  (store_valid_i & store_core_i)
    , .en_b_i     ((store_valid_i && store_core_i) || core_1_rd_i)
    , .rd_data_b_o(core_1_data_o)
);

// Count number of populated instructions
always_comb begin : p_count
    // Initialise state
    `INIT_D(populated_0);
    `INIT_D(populated_1);

    // Count instructions being written
    if (store_valid_i && !store_core_i)
        populated_0 = populated_0 + { {(INSTR_ADDR_W-1){1'b0}}, 1'b1 };
    if (store_valid_i &&  store_core_i)
        populated_1 = populated_1 + { {(INSTR_ADDR_W-1){1'b0}}, 1'b1 };
end

endmodule : nx_instr_store
