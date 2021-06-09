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

// nx_transmitter
// Transmit data onto a bus of any width using strides of a specified size. The
// strobe signal provided with the data indicates which chunks need to be sent
// onto the interface.
//
module nx_transmitter #(
      parameter BUS_WIDTH      =  8 // Width of the bus
    , parameter MAX_DATA_WIDTH = 32 // Maximum data word width
    , parameter FIFO_DEPTH     =  2 // Depth of transmit FIFO
    , parameter MAX_TICKS      = (MAX_DATA_WIDTH + (BUS_WIDTH - 1)) / BUS_WIDTH
) (
      input  logic                      clk_i
    , input  logic                      rst_i
    // Data interface
    , input  logic [MAX_DATA_WIDTH-1:0] tx_data_i
    , input  logic [     MAX_TICKS-1:0] tx_strb_i
    , input  logic                      tx_valid_i
    , output logic                      tx_ready_o
    // Bus interface
    , output logic [     BUS_WIDTH-1:0] bus_data_o
    , output logic                      bus_last_o
    , output logic                      bus_valid_o
    , input  logic                      bus_ready_i
);

// FIFO interfaces
logic m_fifo_empty, m_fifo_full;

assign tx_ready_o = ~m_fifo_full;

// Transmit management
always_comb begin : c_transmit

end

// Transmit FIFO instance
nx_fifo #(
      .DEPTH(FIFO_DEPTH                )
    , .WIDTH(MAX_DATA_WIDTH + MAX_TICKS)
) m_fifo (
      .clk_i    (clk_i                   )
    , .rst_i    (rst_i                   )
    , .wr_data_i({tx_data_i, tx_strb_i}  )
    , .wr_push_i(tx_valid_i && tx_ready_o)
    , .rd_data_o()
    , .rd_pop_o ()
    , .level    ()
    , .empty    (m_fifo_empty            )
    , .full     (m_fifo_full             )
);

endmodule
