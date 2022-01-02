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
      parameter ADDRESS_WIDTH = 10
    , parameter DATA_WIDTH    = 32
    , parameter DEPTH         = 1024
    , parameter REGISTER_A_RD = 0
    , parameter REGISTER_B_RD = 0
    , parameter BYTE_WR_EN_A  = 0
    , parameter BYTE_WR_EN_B  = 0
    , parameter WSTRB_A_WIDTH = (BYTE_WR_EN_A ? (DATA_WIDTH / 8) : 1)
    , parameter WSTRB_B_WIDTH = (BYTE_WR_EN_B ? (DATA_WIDTH / 8) : 1)
) (
    // Port A
      input  logic                     i_clk_a
    , input  logic                     i_rst_a
    , input  logic [ADDRESS_WIDTH-1:0] i_addr_a
    , input  logic [   DATA_WIDTH-1:0] i_wr_data_a
    , input  logic [WSTRB_A_WIDTH-1:0] i_wr_en_a
    , input  logic                     i_en_a
    , output logic [   DATA_WIDTH-1:0] o_rd_data_a
    // Port B
    , input  logic                     i_clk_b
    , input  logic                     i_rst_b
    , input  logic [ADDRESS_WIDTH-1:0] i_addr_b
    , input  logic [   DATA_WIDTH-1:0] i_wr_data_b
    , input  logic [WSTRB_B_WIDTH-1:0] i_wr_en_b
    , input  logic                     i_en_b
    , output logic [   DATA_WIDTH-1:0] o_rd_data_b
);

// =============================================================================
// Constants
// =============================================================================

localparam FULL_WSTRB_WIDTH = (DATA_WIDTH / 8);

// =============================================================================
// Resolve Write Strobes
// =============================================================================

logic [FULL_WSTRB_WIDTH-1:0] wstrb_a, wstrb_b;

generate
if (BYTE_WR_EN_A) begin
    assign wstrb_a = i_wr_en_a;
end else begin
    assign wstrb_a = {FULL_WSTRB_WIDTH{i_wr_en_a}};
end
endgenerate

generate
if (BYTE_WR_EN_B) begin
    assign wstrb_b = i_wr_en_b;
end else begin
    assign wstrb_b = {FULL_WSTRB_WIDTH{i_wr_en_b}};
end
endgenerate

// =============================================================================
// RAM Simulation Model
// =============================================================================

`ifdef USE_RAM_MODEL

reg [DATA_WIDTH-1:0] memory [DEPTH-1:0];

logic [DATA_WIDTH-1:0] rd_a_data_q, rd_a_data_dly_q;
logic [DATA_WIDTH-1:0] rd_b_data_q, rd_b_data_dly_q;

// Create bitwise masks
logic [DATA_WIDTH-1:0] wmask_a, wmask_b;

generate
for (genvar idx = 0; idx < (DATA_WIDTH / 8); idx++) begin : gen_wmask
    assign wmask_a[(idx*8)+:8] = {8{wstrb_a[idx]}};
    assign wmask_b[(idx*8)+:8] = {8{wstrb_b[idx]}};
end
endgenerate

// Optional pipelining of output
assign o_rd_data_a = REGISTER_A_RD ? rd_a_data_dly_q : rd_a_data_q;
assign o_rd_data_b = REGISTER_B_RD ? rd_b_data_dly_q : rd_b_data_q;

always_ff @(posedge i_clk_a, posedge i_rst_a) begin : ff_read_a
    if (i_rst_a) begin
        rd_a_data_q     <= 'd0;
        rd_a_data_dly_q <= 'd0;
    end else begin
        rd_a_data_dly_q <= rd_a_data_q;
        if (i_en_a) begin
            if (|i_wr_en_a) begin
                memory[i_addr_a] <= (
                    (i_wr_data_a      &  wmask_a) |
                    (memory[i_addr_a] & ~wmask_a)
                );
            end else begin
                rd_a_data_q <= memory[i_addr_a];
            end
        end
    end
end

always_ff @(posedge i_clk_b, posedge i_rst_b) begin : ff_read_b
    if (i_rst_b) begin
        rd_b_data_q     <= 'd0;
        rd_b_data_dly_q <= 'd0;
    end else begin
        rd_b_data_dly_q <= rd_b_data_q;
        if (i_en_b) begin
            if (|i_wr_en_b) begin
                memory[i_addr_b] <= (
                    (i_wr_data_b      &  wmask_b) |
                    (memory[i_addr_b] & ~wmask_b)
                );
            end else begin
                rd_b_data_q <= memory[i_addr_b];
            end
        end
    end
end

// Aliases for VCD tracing
`ifdef sim_icarus
    `ifdef TRACE_RAM
generate
    genvar idx;
    for (idx = 0; idx < DEPTH; idx = (idx + 1)) begin
        wire [DATA_WIDTH-1:0] memory_alias = memory[idx];
    end
endgenerate
    `endif
`endif // sim_icarus

// =============================================================================
// FPGA RAM Instance
// =============================================================================

`else

// Extract read data
logic [35:0] read_data [1:0];
assign o_rd_data_a = read_data[0][DATA_WIDTH-1:0];
assign o_rd_data_b = read_data[1][DATA_WIDTH-1:0];

// Pad write data
logic [35:0] write_data [1:0];
assign write_data[0] = { {(36-DATA_WIDTH){1'b0}}, i_wr_data_a };
assign write_data[1] = { {(36-DATA_WIDTH){1'b0}}, i_wr_data_b };

RAMB36E1 #(
      .RDADDR_COLLISION_HWCONFIG ( "PERFORMANCE" ) // No collision possible
    , .SIM_COLLISION_CHECK       ( "ALL"         ) // Warn about any collisions
    , .DOA_REG                   ( REGISTER_A_RD ) // Read output A pipelining
    , .DOB_REG                   ( REGISTER_B_RD ) // Read output B pipelining
    , .EN_ECC_READ               ( "FALSE"       ) // Disable ECC read decoder
    , .EN_ECC_WRITE              ( "FALSE"       ) // Disable ECC write encoder
    , .INIT_A                    ( 36'h000000000 ) // Initial output A port value
    , .INIT_B                    ( 36'h000000000 ) // Initial output B port value
    , .RAM_MODE                  ( "TDP"         ) // True dual-port mode
    , .RAM_EXTENSION_A           ( "NONE"        ) // No cascading
    , .RAM_EXTENSION_B           ( "NONE"        ) // No cascading
    , .READ_WIDTH_A              ( 36            ) // 36-bit read port A
    , .READ_WIDTH_B              ( 36            ) // 36-bit read port B
    , .WRITE_WIDTH_A             ( 36            ) // 36-bit write port A
    , .WRITE_WIDTH_B             ( 36            ) // 36-bit write port B
    , .RSTREG_PRIORITY_A         ( "RSTREG"      ) // Reset or enable priority A
    , .RSTREG_PRIORITY_B         ( "RSTREG"      ) // Reset or enable priority B
    , .SRVAL_A                   ( 36'h000000000 ) // Set/reset value for output A
    , .SRVAL_B                   ( 36'h000000000 ) // Set/reset value for output B
    , .SIM_DEVICE                ( "7SERIES"     ) // Simulation behaviour
    , .WRITE_MODE_A              ( "WRITE_FIRST" ) // Output write value onto read bus A
    , .WRITE_MODE_B              ( "WRITE_FIRST" ) // Output write value onto read bus B
) ram_inst (
    // RAM cascading ports - not used here
      .CASCADEOUTA   (                                                )
    , .CASCADEOUTB   (                                                )
    , .CASCADEINA    ( 1'b0                                           )
    , .CASCADEINB    ( 1'b0                                           )
    // ECC signals - not used here
    , .DBITERR       (                                                )
    , .ECCPARITY     (                                                )
    , .RDADDRECC     (                                                )
    , .SBITERR       (                                                )
    , .INJECTDBITERR ( 1'b0                                           )
    , .INJECTSBITERR ( 1'b0                                           )
    // Port A
    , .CLKARDCLK     ( i_clk_a                                        )
    , .ADDRARDADDR   ( { {(10-ADDRESS_WIDTH){1'b0}}, i_addr_a, 5'd0 } )
    , .ENARDEN       ( i_en_a                                         )
    , .REGCEAREGCE   ( 1'b0                                           )
    , .RSTRAMARSTRAM ( 1'b0                                           )
    , .RSTREGARSTREG ( 1'b0                                           )
    , .WEA           ( wstrb_a                                        )
    , .DIADI         ( write_data[0][31: 0]                           )
    , .DIPADIP       ( write_data[0][35:32]                           )
    , .DOADO         ( read_data[0][31: 0]                            )
    , .DOPADOP       ( read_data[0][35:32]                            )
    // Port B
    , .CLKBWRCLK     ( i_clk_b                                        )
    , .ADDRBWRADDR   ( { {(10-ADDRESS_WIDTH){1'b0}}, i_addr_b, 5'd0 } )
    , .ENBWREN       ( i_en_b                                         )
    , .REGCEB        ( 1'b0                                           )
    , .RSTRAMB       ( 1'b0                                           )
    , .RSTREGB       ( 1'b0                                           )
    , .WEBWE         ( wstrb_b                                        )
    , .DIBDI         ( write_data[1][31: 0]                           )
    , .DIPBDIP       ( write_data[1][35:32]                           )
    , .DOBDO         ( read_data[1][31: 0]                            )
    , .DOPBDOP       ( read_data[1][35:32]                            )
);

`endif

endmodule
