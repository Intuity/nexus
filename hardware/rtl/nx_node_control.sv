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
`include "nx_commands.svh"

module nx_node_control #(
    // Command interface parameters
      parameter TARGET_W  =  8
    , parameter CMD_W     =  8
    , parameter PAYLOAD_W = 24
    , parameter VALID_W   = (PAYLOAD_W / CMD_W)
    // Logic core parameters
    , parameter OP_W   =  4
    , parameter REG_W  = 16
    , parameter IO_W   =  4
    , parameter SLOTS  = 32
    , parameter INST_W = OP_W + (3 * $clog2(REG_W)) + 1 + $clog2(IO_W)
) (
      input  logic                     clk
    , input  logic                     rst
    // Core control
    , output logic                     stall
    // Receive interface
    , input  logic [        CMD_W-1:0] rx_command
    , input  logic [    PAYLOAD_W-1:0] rx_payload
    , input  logic [      VALID_W-1:0] rx_valid
    , input  logic                     rx_complete
    , output logic                     rx_ready
    // Instruction load
    , output logic [       INST_W-1:0] load_instr
    , output logic [$clog2(SLOTS)-1:0] load_slot
    , output logic                     load_last
    , output logic                     load_valid
    // Input load
    , output logic                     in_value
    , output logic [ $clog2(IO_W)-1:0] in_index
    , output logic                     in_valid
    // Value output
    , input  logic [         IO_W-1:0] out_values
    , input  logic [         IO_W-1:0] out_valids
    // Transmit interface
    , output logic [     TARGET_W-1:0] tx_target
    , output logic [        CMD_W-1:0] tx_command
    , output logic [    PAYLOAD_W-1:0] tx_payload
    , output logic [      VALID_W-1:0] tx_valid
    , input  logic                     tx_ready
);

localparam SLOT_W = $clog2(SLOTS);

// TODO: Drive signals properly
assign rx_ready = 1'b1;

// Instruction load
logic [INST_W-1:0] `DECLARE_DQ(instr_data,  clk, rst, {INST_W{1'b0}})
logic [SLOT_W-1:0] `DECLARE_DQ(instr_slot,  clk, rst, {SLOT_W{1'b0}})
logic              `DECLARE_DQ(instr_last,  clk, rst,           1'b0)
logic              `DECLARE_DQ(instr_valid, clk, rst,           1'b0)

assign load_instr = m_instr_data_q;
assign load_slot  = m_instr_slot_q;
assign load_last  = m_instr_last_q;
assign load_valid = m_instr_valid_q;

// Input load
logic                    `DECLARE_DQ(input_value, clk, rst,                 1'b0)
logic [$clog2(IO_W)-1:0] `DECLARE_DQ(input_index, clk, rst, {$clog2(IO_W){1'b0}})
logic                    `DECLARE_DQ(input_valid, clk, rst,                 1'b0)

assign in_value = m_input_value_q;
assign in_index = m_input_index_q;
assign in_valid = m_input_valid_q;

// Output->input mapping
logic [$clog2(IO_W)-1:0] m_output_map_d [IO_W-1:0];
logic [$clog2(IO_W)-1:0] m_output_map_q [IO_W-1:0];

// Command transmit
logic [ TARGET_W-1:0] `DECLARE_DQ(tx_target,  clk, rst,  {TARGET_W{1'b0}})
logic [    CMD_W-1:0] `DECLARE_DQ(tx_command, clk, rst,     {CMD_W{1'b0}})
logic [PAYLOAD_W-1:0] `DECLARE_DQ(tx_payload, clk, rst, {PAYLOAD_W{1'b0}})
logic [  VALID_W-1:0] `DECLARE_DQ(tx_valid,   clk, rst,   {VALID_W{1'b0}})

assign tx_target  = m_tx_target_q;
assign tx_command = m_tx_command_q;
assign tx_payload = m_tx_payload_q;
assign tx_valid   = m_tx_valid_q;

// Control stall
assign stall = (~tx_ready || tx_valid) & (out_valids != {IO_W{1'b0}});

// c_decode_rx
// Decode received commands and generate instruction/input load to core
//
always_comb begin : c_decode_rx
    integer      i;
    nx_command_t command;
    logic [4:0]  index;

    `INIT_D(instr_data);
    `INIT_D(instr_slot);
    `INIT_D(instr_last);
    `INIT_D(instr_valid);

    `INIT_D(input_value);
    `INIT_D(input_index);
    `INIT_D(input_valid);

    for (i = 0; i < IO_W; i = (i + 1)) m_output_map_d[i] = m_output_map_q[i];

    // Always clear valid signals
    m_instr_valid_d = 1'b0;
    m_input_valid_d = 1'b0;

    // If a command is presented, process it
    if (rx_complete) begin
        // Common decode
        { command, index } = rx_command;

        // Perform command specific actions
        case (command)
            CMD_LOAD_INSTR, CMD_LAST_INSTR: begin
                m_instr_data_d  = rx_payload;
                m_instr_slot_d  = index;
                m_instr_last_d  = (command == CMD_LAST_INSTR);
                m_instr_valid_d = 1'b1;
            end
            CMD_BIT_VALUE: begin
                m_input_value_d = rx_payload[0];
                m_input_index_d = index[$clog2(IO_W)-1:0];
                m_input_valid_d = 1'b1;
            end
            CMD_OUT_MAP: begin
                // Encoding: { INPUT_IDX, OUTPUT_IDX }
                m_output_map_d[rx_payload[$clog2(IO_W)-1:0]] = rx_payload[(2*$clog2(IO_W))-1:$clog2(IO_W)];
            end
        endcase
    end
end

// c_encode_tx
// Encode messages to transmit to other cores and boundary I/O
//
always_comb begin : c_encode_tx
    integer i;

    `INIT_D(tx_target);
    `INIT_D(tx_command);
    `INIT_D(tx_payload);
    `INIT_D(tx_valid);

    if (tx_ready) begin
        // Clear the valid as it has been accepted
        m_tx_valid_d = 1'b0;

        // If any output has been updated, send out required messages
        // NOTE: For now assume only 1 bit will ever be high
        if (out_valids != {IO_W{1'b0}}) begin
            for (i = 0; i < IO_W; i = (i + 1)) begin
                if (out_valids[i]) begin
                    m_tx_target_d  = 8'd0; // TODO: Use real target
                    m_tx_command_d = {
                        CMD_BIT_VALUE,            // Base command
                        {(5-$clog2(IO_W)){1'b0}}, // Padding
                        m_output_map_q[i]         // Map output -> input bit
                    };
                    m_tx_payload_d = { 7'd0, out_values[i] };
                    m_tx_valid_d   = 1'b1;
                end
            end
        end
    end
end

// s_output_map
// Handle D->Q transfer for output map
//
always_ff @(posedge clk, posedge rst) begin : s_output_map
    integer i;
    if (rst) begin
        for (i = 0; i < IO_W; i = (i + 1)) m_output_map_q[i] <= {$clog2(IO_W){1'b0}};
    end else begin
        for (i = 0; i < IO_W; i = (i + 1)) m_output_map_q[i] <= m_output_map_d[i];
    end
end

// Aliases for VCD tracing
`ifndef SYNTHESIS
generate
    genvar idx;
    for (idx = 0; idx < IO_W; idx = (idx + 1)) begin : m_alias
        logic [$clog2(IO_W)-1:0] m_output_map_alias;
        assign m_output_map_alias = m_output_map_q[idx];
    end
endgenerate
`endif

endmodule
