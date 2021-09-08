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
// Dual ported data store - first port is used for the instruction sequence,
// second port is used for the control block
//
module nx_node_store
import NXConstants::*;
#(
      parameter MAX_INSTRS  = 512 // Maximum number of instructions per core
    , parameter CTRL_WIDTH  =  13 // Width of each control entry
    , parameter MAX_CTRL    = 512 // Maximum number of control entries
) (
      input  logic clk_i
    , input  logic rst_i
    // Populated instruction counter
    , output logic [$clog2(MAX_INSTRS)-1:0] instr_count_o
    // Instruction load interface
    , input  instruction_t store_data_i
    , input  logic         store_valid_i
    // Instruction fetch interfaces
    , input  logic [$clog2(MAX_INSTRS)-1:0] fetch_addr_i
    , input  logic                          fetch_rd_i
    , output instruction_t                  fetch_data_o
    , output logic                          fetch_stall_o
    // Control block interface
    , input  logic [$clog2(MAX_CTRL)-1:0] ctrl_addr_i
    , input  logic [      CTRL_WIDTH-1:0] ctrl_wr_data_i
    , input  logic                        ctrl_wr_en_i
    , input  logic                        ctrl_rd_en_i
    , output logic [      CTRL_WIDTH-1:0] ctrl_rd_data_o
);

// Parameters
localparam INSTR_WIDTH  = $bits(instruction_t);
localparam INSTR_ADDR_W = $clog2(MAX_INSTRS);
localparam CTRL_ADDR_W  = $clog2(MAX_CTRL);
localparam MAX_ADDR_W   = (INSTR_ADDR_W > CTRL_ADDR_W) ? INSTR_ADDR_W : CTRL_ADDR_W;
localparam MAX_DATA_W   = (INSTR_WIDTH  > CTRL_WIDTH ) ? INSTR_WIDTH  : CTRL_WIDTH;

// Internal state
logic [INSTR_ADDR_W-1:0] instr_count_q;

// Construct outputs
assign instr_count_o = instr_count_q;
assign fetch_stall_o = store_valid_i;

// Hookup RAM
logic [MAX_DATA_W-1:0] rd_data_a, rd_data_b;

assign fetch_data_o   = rd_data_a[INSTR_WIDTH-1:0];
assign ctrl_rd_data_o = rd_data_b[ CTRL_WIDTH-1:0];

nx_ram #(
      .ADDRESS_WIDTH(MAX_ADDR_W + 1)
    , .DATA_WIDTH   (MAX_DATA_W    )
) ram (
    // Port A
      .clk_a_i    (clk_i)
    , .rst_a_i    (rst_i)
    , .addr_a_i   ({
        1'b0,                              // MSB low for instruction store
        {(MAX_ADDR_W-INSTR_ADDR_W){1'b0}}, // Padding
        store_valid_i ? instr_count_q : fetch_addr_i
    })
    , .wr_data_a_i({ {(MAX_DATA_W-INSTR_WIDTH){1'b0}}, store_data_i })
    , .wr_en_a_i  (store_valid_i)
    , .en_a_i     (store_valid_i || fetch_rd_i)
    , .rd_data_a_o(rd_data_a)
    // Port B
    , .clk_b_i    (clk_i)
    , .rst_b_i    (rst_i)
    , .addr_b_i   ({
        1'b1,                             // MSB high for control store
        {(MAX_ADDR_W-CTRL_ADDR_W){1'b0}}, // Padding
        ctrl_addr_i
    })
    , .wr_data_b_i({ {(MAX_DATA_W-CTRL_WIDTH){1'b0}}, ctrl_wr_data_i })
    , .wr_en_b_i  (ctrl_wr_en_i)
    , .en_b_i     (ctrl_wr_en_i || ctrl_rd_en_i)
    , .rd_data_b_o(rd_data_b)
);

// Count stored instructions
always_ff @(posedge clk_i, posedge rst_i) begin : p_count
    if (rst_i) begin
        instr_count_q <= {INSTR_ADDR_W{1'b0}};
    end else begin
        if (store_valid_i)
            instr_count_q <= instr_count_q + { {(INSTR_ADDR_W-1){1'b0}}, 1'b1 };
    end
end

endmodule : nx_node_store
