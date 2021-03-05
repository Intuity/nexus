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
      parameter TARGET_W =  8 // Address width for targets
    , parameter CMD_W    =  8 // Command bus width
    // Logic core parameters
    , parameter OP_W     =  4 // Operand encoding width
    , parameter REG_W    = 16 // Internal register width
    , parameter IO_W     =  4 // Primary inputs/outputs width
    , parameter SLOTS    = 32 // How many instruction slots are available
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

localparam PAYLOAD_W = 24;
localparam INST_W    = OP_W + (3 * $clog2(REG_W)) + 1 + $clog2(IO_W);

logic m_stall;

logic [            CMD_W-1:0] m_rx_command;
logic [        PAYLOAD_W-1:0] m_rx_payload;
logic [(PAYLOAD_W/CMD_W)-1:0] m_rx_valid;
logic                         m_rx_complete;
logic                         m_rx_ready;

logic [       INST_W-1:0] m_load_instr;
logic [$clog2(SLOTS)-1:0] m_load_slot;
logic                     m_load_last;
logic                     m_load_valid;

logic                    m_in_value;
logic [$clog2(IO_W)-1:0] m_in_index;
logic                    m_in_valid;

logic [IO_W-1:0] m_out_values;
logic [IO_W-1:0] m_out_valids;

logic [         TARGET_W-1:0] m_tx_target;
logic [            CMD_W-1:0] m_tx_command;
logic [        PAYLOAD_W-1:0] m_tx_payload;
logic [(PAYLOAD_W/CMD_W)-1:0] m_tx_valid;
logic                         m_tx_ready;

// Controller
nx_node_control #(
      .TARGET_W (TARGET_W )
    , .CMD_W    (CMD_W    )
    , .PAYLOAD_W(PAYLOAD_W)
) m_control (
      .clk(clk)
    , .rst(rst)
    // Core control
    , .stall(m_stall)
    // Receive interface
    , .rx_command (m_rx_command )
    , .rx_payload (m_rx_payload )
    , .rx_valid   (m_rx_valid   )
    , .rx_complete(m_rx_complete)
    , .rx_ready   (m_rx_ready   )
    // Instruction load
    , .load_instr(m_load_instr)
    , .load_slot (m_load_slot )
    , .load_last (m_load_last )
    , .load_valid(m_load_valid)
    // Input load
    , .in_value(m_in_value)
    , .in_index(m_in_index)
    , .in_valid(m_in_valid)
    // Value output
    , .out_values(m_out_values)
    , .out_valids(m_out_valids)
    // Transmit interface
    , .tx_target (m_tx_target )
    , .tx_command(m_tx_command)
    , .tx_payload(m_tx_payload)
    , .tx_valid  (m_tx_valid  )
    , .tx_ready  (m_tx_ready  )
);

// Receive instructions and input signal state
nx_receiver #(
      .TARGET_W ( TARGET_W)
    , .BUS_W    (    CMD_W)
    , .PAYLOAD_W(PAYLOAD_W)
) m_cmd_rx (
      .clk(clk)
    , .rst(rst)
    // Command interface
    , .cmd_data (rx_cmd_data )
    , .cmd_last (rx_cmd_last )
    , .cmd_valid(rx_cmd_valid)
    , .cmd_ready(rx_cmd_ready)
    // Data received
    , .rx_command (m_rx_command )
    , .rx_payload (m_rx_payload )
    , .rx_valid   (m_rx_valid   )
    , .rx_complete(m_rx_complete)
    , .rx_ready   (m_rx_ready   )
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
    , .tick (tick   )
    , .stall(m_stall)
    // State outputs
    , .in_setup(in_setup)
    , .in_wait (in_wait )
    , .in_run  (in_run  )
    // Instruction load
    , .load_instr(m_load_instr)
    , .load_slot (m_load_slot )
    , .load_last (m_load_last )
    , .load_valid(m_load_valid)
    // Input load
    , .in_value(m_in_value)
    , .in_index(m_in_index)
    , .in_valid(m_in_valid)
    // Value output
    , .out_values(m_out_values)
    , .out_valids(m_out_valids)
);

// Transmit output signal state
nx_transmitter #(
      .TARGET_W ( TARGET_W)
    , .BUS_W    (    CMD_W)
    , .PAYLOAD_W(PAYLOAD_W)
) m_cmd_tx (
      .clk(clk)
    , .rst(rst)
    // Data to send
    , .tx_command(m_tx_command)
    , .tx_payload(m_tx_payload)
    , .tx_valid  (m_tx_valid  )
    , .tx_ready  (m_tx_ready  )
    // Command interface
    , .cmd_data (tx_cmd_data )
    , .cmd_last (tx_cmd_last )
    , .cmd_valid(tx_cmd_valid)
    , .cmd_ready(tx_cmd_ready)
);

endmodule
