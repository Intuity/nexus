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

// nx_ram
// 36 Kib dual-port RAM intended to map directly to a Xilinx RAMB36 instance
//
module nx_ram #(
      parameter ADDRESS_WIDTH = 16
    , parameter DATA_WIDTH    = 36
    , parameter DEPTH         = 1024
) (
    // Port A
      input  logic                     clk_a_i
    , input  logic                     rst_a_i
    , input  logic [ADDRESS_WIDTH-1:0] addr_a_i
    , input  logic [   DATA_WIDTH-1:0] wr_data_a_i
    , input  logic                     wr_en_a_i
    , input  logic                     en_a_i
    , output logic [   DATA_WIDTH-1:0] rd_data_a_o
    // Port B
    , input  logic                     clk_b_i
    , input  logic                     rst_b_i
    , input  logic [ADDRESS_WIDTH-1:0] addr_b_i
    , input  logic [   DATA_WIDTH-1:0] wr_data_b_i
    , input  logic                     wr_en_b_i
    , input  logic                     en_b_i
    , output logic [   DATA_WIDTH-1:0] rd_data_b_o
);

reg [DATA_WIDTH-1:0] m_memory [DEPTH-1:0];

always_ff @(posedge clk_a_i, posedge rst_a_i) begin : ff_read_a
    if (rst_a_i) begin
        rd_data_a_o <= {DATA_WIDTH{1'b0}};
    end else begin
        if (en_a_i) begin
            if (wr_en_a_i) begin
                m_memory[addr_a_i[$clog2(DEPTH-1):0]] <= wr_data_a_i;
            end else begin
                rd_data_a_o <= m_memory[addr_a_i[$clog2(DEPTH-1):0]];
            end
        end
    end
end

always_ff @(posedge clk_b_i, posedge rst_b_i) begin : ff_read_b
    if (rst_b_i) begin
        rd_data_b_o <= {DATA_WIDTH{1'b0}};
    end else begin
        if (en_b_i) begin
            if (wr_en_b_i) begin
                m_memory[addr_b_i[$clog2(DEPTH-1):0]] <= wr_data_b_i;
            end else begin
                rd_data_b_o <= m_memory[addr_b_i[$clog2(DEPTH-1):0]];
            end
        end
    end
end

endmodule
