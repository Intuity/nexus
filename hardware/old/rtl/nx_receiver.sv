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

// nx_receiver
// Receive data from a bus of any width and reconstruct into messages. The data
// is always padded out to align it to the least significant bit of the buffer.
//
module nx_receiver #(
      parameter BUS_WIDTH      =  8 // Width of the bus
    , parameter MAX_DATA_WIDTH = 32 // Maximum data word width
    , parameter FIFO_DEPTH     =  2 // Depth of receive FIFO
) (
      input  logic                      clk_i
    , input  logic                      rst_i
    // Bus interface
    , input  logic [     BUS_WIDTH-1:0] bus_data_i
    , input  logic                      bus_last_i
    , input  logic                      bus_valid_i
    , output logic                      bus_ready_o
    // Data interface
    , output logic [MAX_DATA_WIDTH-1:0] rx_data_o
    , output logic                      rx_valid_o
    , input  logic                      rx_ready_i
);

// Constants
localparam MAX_TICKS  = (MAX_DATA_WIDTH + (BUS_WIDTH - 1)) / BUS_WIDTH;
localparam TICK_WIDTH = $clog2(MAX_TICKS) + 1;
localparam TICK_STEP  = { {(TICK_WIDTH-1){1'b0}}, 1'b1 };

// State
logic [MAX_DATA_WIDTH-1:0] `DECLARE_DQ(accum,    clk, rst, {MAX_DATA_WIDTH{1'b0}})
logic [    TICK_WIDTH-1:0] `DECLARE_DQ(ticks,    clk, rst, {    TICK_WIDTH{1'b0}})
logic                      `DECLARE_DQ(overflow, clk, rst,                   1'b0)
logic                      `DECLARE_DQ(complete, clk, rst,                   1'b0)

// FIFO interfaces
logic m_fifo_empty, m_fifo_full;

assign rx_valid_o  = ~m_fifo_empty;
assign bus_ready_o = ~m_fifo_full;

// Receive management
always_comb begin : c_receive
    reg [TICK_WIDTH-1:0] idx;

    // Initialise state
    `INIT_D(accum);
    `INIT_D(ticks);
    `INIT_D(overflow);

    // After complete was high for a cycle, clear state
    if (m_complete_d) begin
        m_ticks_d    = {TICK_WIDTH{1'b0}};
        m_overflow_d = 1'b0;
        m_complete_d = 1'b0;
    end

    // Wait for a new stride
    if (bus_valid_i && bus_ready_o) begin
        // If ticks already max, mark an overflow
        if (m_ticks_d >= MAX_TICKS) m_overflow_d = 1'b1;

        // Feed the accumulator
        m_accum_d = { bus_data_i, m_accum_d[MAX_DATA_WIDTH-1:BUS_WIDTH] };

        // Increment the number of ticks
        m_ticks_d = (m_ticks_d + TICK_STEP);

        // On the last cycle...
        if (bus_last_i) begin
            // Align the data to the bottom of the buffer
            for (idx = 0; i < (MAX_TICKS - m_ticks_d); idx = (idx + TICK_STEP)) begin
                m_accum_d = { {BUS_WIDTH{1'b0}}, m_accum_d[MAX_DATA_WIDTH-1:BUS_WIDTH] };
            end
            // Mark the transaction as complete (pushes into the FIFO)
            m_complete_d = 1'b1;
        end
    end
end

// Receive FIFO instance
nx_fifo #(
      .DEPTH(FIFO_DEPTH    )
    , .WIDTH(MAX_DATA_WIDTH)
) m_fifo (
      .clk_i    (clk_i                        )
    , .rst_i    (rst_i                        )
    , .wr_data_i(m_accum_q                    )
    , .wr_push_i(m_complete_q && !m_overflow_q)
    , .rd_data_o(rx_data_o                    )
    , .rd_pop_o (rx_ready_i && rx_valid_o     )
    , .level    (                             )
    , .empty    (m_fifo_empty                 )
    , .full     (m_fifo_full                  )
);

endmodule : nx_receiver
