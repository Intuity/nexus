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

module nx_node #(
    // Command interface parameters
      parameter CMD_W  =  8
    // Node core parameters
    , parameter OP_W   =  4 // Operand encoding width
    , parameter REG_W  = 16 // Internal register width
    , parameter IO_W   =  4 // Primary inputs/outputs width
    , parameter SLOTS  = 32 // How many instruction slots are available
) (
      input  logic clk
    , input  logic rst
    // External controls
    , input  logic tick
    // State outputs
    , output logic in_setup
    , output logic in_wait
    , output logic in_run
    // Inbound command
    , input  logic [CMD_W-1:0] rx_cmd_data
    , input  logic             rx_cmd_last
    , input  logic             rx_cmd_valid
    , output logic             rx_cmd_ready
    // Outbound command
    , output logic [CMD_W-1:0] tx_cmd_data
    , output logic             tx_cmd_last
    , output logic             tx_cmd_valid
    , input  logic             tx_cmd_ready
);

// Receive instructions and input signal state
nx_receiver #(
      .BUS_W    (CMD_W)
    , .PAYLOAD_W(   24)
) m_cmd_rx (
      .clk(clk)
    , .rst(rst)
    // Command interface
    , .cmd_data (rx_cmd_data )
    , .cmd_last (rx_cmd_last )
    , .cmd_valid(rx_cmd_valid)
    , .cmd_ready(rx_cmd_ready)
    // Data received
    , .rx_command()
    , .rx_payload()
    , .rx_valid  ()
    , .rx_ready  ()
);

// Execute logic code
nx_node_core #(
      .OP_W (OP_W )
    , .REG_W(REG_W)
    , .IO_W (IO_W )
    , .SLOTS(SLOTS)
) m_core (
      .clk(clk)
    , .rst(rst)
    // External controls
    , .tick(tick)
    // State outputs
    , .in_setup(in_setup)
    , .in_wait (in_wait )
    , .in_run  (in_run  )
    // Instruction load
    , .load_instr()
    , .load_slot ()
    , .load_valid()
    // Input load
    , .in_value()
    , .in_index()
    , .in_valid()
    // Value output
    , .out_values()
    , .out_valids()
);

// Transmit output signal state
nx_transmitter #(
      .BUS_W    (CMD_W)
    , .PAYLOAD_W(   24)
) m_cmd_tx (
      .clk(clk)
    , .rst(rst)
    // Data to send
    , .tx_command()
    , .tx_payload()
    , .tx_valid  ()
    , .tx_ready  ()
    // Command interface
    , .cmd_data (tx_cmd_data )
    , .cmd_last (tx_cmd_last )
    , .cmd_valid(tx_cmd_valid)
    , .cmd_ready(tx_cmd_ready)
);

endmodule
