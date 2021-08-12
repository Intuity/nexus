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

`ifdef sim_icarus

reg [DATA_WIDTH-1:0] memory [DEPTH-1:0];

always_ff @(posedge clk_a_i, posedge rst_a_i) begin : ff_read_a
    if (rst_a_i) begin
        rd_data_a_o <= {DATA_WIDTH{1'b0}};
    end else begin
        if (en_a_i) begin
            if (wr_en_a_i) begin
                memory[addr_a_i] <= wr_data_a_i;
            end else begin
                rd_data_a_o <= memory[addr_a_i];
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
                memory[addr_b_i] <= wr_data_b_i;
            end else begin
                rd_data_b_o <= memory[addr_b_i];
            end
        end
    end
end

`else

logic [35:0] read_data [1:0], write_data [1:0];

assign rd_data_a_o = read_data[0][DATA_WIDTH-1:0];
assign rd_data_b_o = read_data[1][DATA_WIDTH-1:0];

assign write_data[0] = { {(DATA_WIDTH-1){1'b0}}, wr_data_a_i };
assign write_data[1] = { {(DATA_WIDTH-1){1'b0}}, wr_data_b_i };

RAMB36E1 #(
      .RDADDR_COLLISION_HWCONFIG("PERFORMANCE") // No collision possible
    , .SIM_COLLISION_CHECK      ("ALL")         // Warn about any collisions
    , .DOA_REG                  (0)             // Disable output A being pipelined
    , .DOB_REG                  (0)             // Disable output B being pipelined
    , .EN_ECC_READ              ("FALSE")       // Disable ECC read decoder
    , .EN_ECC_WRITE             ("FALSE")       // Disable ECC write encoder
    , .INIT_A                   (36'h000000000) // Initial output A port value
    , .INIT_B                   (36'h000000000) // Initial output B port value
    , .RAM_MODE                 ("TDP")         // True dual-port mode
    , .RAM_EXTENSION_A          ("NONE")        // No cascading
    , .RAM_EXTENSION_B          ("NONE")        // No cascading
    , .READ_WIDTH_A             (36)            // 36-bit read port A
    , .READ_WIDTH_B             (36)            // 36-bit read port B
    , .WRITE_WIDTH_A            (36)            // 36-bit write port A
    , .WRITE_WIDTH_B            (36)            // 36-bit write port B
    , .RSTREG_PRIORITY_A        ("RSTREG")      // Reset or enable priority A
    , .RSTREG_PRIORITY_B        ("RSTREG")      // Reset or enable priority B
    , .SRVAL_A                  (36'h000000000) // Set/reset value for output A
    , .SRVAL_B                  (36'h000000000) // Set/reset value for output B
    , .SIM_DEVICE               ("7SERIES")     // Simulation behaviour
    , .WRITE_MODE_A             ("WRITE_FIRST") // Output write value onto read bus A
    , .WRITE_MODE_B             ("WRITE_FIRST") // Output write value onto read bus B
) ram_inst (
    // RAM cascading ports - not used here
      .CASCADEOUTA()
    , .CASCADEOUTB()
    , .CASCADEINA (1'b0)
    , .CASCADEINB (1'b0)
    // ECC signals - not used here
    , .DBITERR      ()
    , .ECCPARITY    ()
    , .RDADDRECC    ()
    , .SBITERR      ()
    , .INJECTDBITERR(1'b0)
    , .INJECTSBITERR(1'b0)
    // Port A
    , .CLKARDCLK    (clk_a_i)
    , .ADDRARDADDR  ({ {(10-ADDRESS_WIDTH){1'b0}}, addr_a_i, 5'd0 })
    , .ENARDEN      (en_a_i)
    , .REGCEAREGCE  (1'b0)
    , .RSTRAMARSTRAM(1'b0)
    , .RSTREGARSTREG(1'b0)
    , .WEA          ({4{wr_en_a_i}})
    , .DIADI        (write_data[0][31: 0])
    , .DIPADIP      (write_data[0][35:32])
    , .DOADO        (read_data[0][31: 0])
    , .DOPADOP      (read_data[0][35:32])
    // Port B
    , .CLKBWRCLK  (clk_b_i)
    , .ADDRBWRADDR({ {(10-ADDRESS_WIDTH){1'b0}}, addr_b_i, 5'd0 })
    , .ENBWREN    (en_b_i)
    , .REGCEB     (1'b0)
    , .RSTRAMB    (1'b0)
    , .RSTREGB    (1'b0)
    , .WEBWE      ({4{wr_en_b_i}})
    , .DIBDI      (write_data[1][31: 0])
    , .DIPBDIP    (write_data[1][35:32])
    , .DOBDO      (read_data[1][31: 0])
    , .DOPBDOP    (read_data[1][35:32])
);

`endif

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

endmodule
