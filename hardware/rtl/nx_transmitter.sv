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

module nx_transmitter #(
      parameter TARGET_W  =  8
    , parameter BUS_W     =  8
    , parameter PAYLOAD_W = 24
) (
      input  logic                         clk
    , input  logic                         rst
    // Data to send
    , input  logic [         TARGET_W-1:0] tx_target
    , input  logic [            BUS_W-1:0] tx_command
    , input  logic [        PAYLOAD_W-1:0] tx_payload
    , input  logic [(PAYLOAD_W/BUS_W)-1:0] tx_valid
    , output logic                         tx_ready
    // Command interface
    , output logic [            BUS_W-1:0] cmd_data
    , output logic                         cmd_last
    , output logic                         cmd_valid
    , input  logic                         cmd_ready
);

typedef enum bit [1:0] {
      TX_TARGET  // Sending target address
    , TX_COMMAND // Sending command
    , TX_PAYLOAD // Sending payload
} nx_tx_state_t;

nx_tx_state_t             `DECLARE_DQ(state);
logic [        BUS_W-1:0] `DECLARE_DQ(command);
logic [    PAYLOAD_W-1:0] `DECLARE_DQ(payload);
logic [(PAYLOAD_W/8)-1:0] `DECLARE_DQ(valids);
logic [        BUS_W-1:0] `DECLARE_DQ(cmd_data);
logic                     `DECLARE_DQ(cmd_last);
logic                     `DECLARE_DQ(cmd_valid);

assign tx_ready  = (m_state_q == TX_TARGET) && cmd_ready;
assign cmd_data  = m_cmd_data_q;
assign cmd_last  = m_cmd_last_q;
assign cmd_valid = m_cmd_valid_q;

always_comb begin : c_transmit
    integer i;

    `INIT_D(state);
    `INIT_D(command);
    `INIT_D(payload);
    `INIT_D(valids);
    `INIT_D(cmd_data);
    `INIT_D(cmd_last);
    `INIT_D(cmd_valid);

    if (cmd_ready) begin
        case (m_state_d)
            // TARGET: Push target address onto bus
            TX_TARGET: begin
                // Capture data
                m_command_d = tx_command;
                m_payload_d = tx_payload;
                m_valids_d  = tx_valid;
                // Setup push onto bus
                m_cmd_data_d  = tx_target;
                m_cmd_last_d  = 1'b0;
                m_cmd_valid_d = |m_valids_d;
                // If target pushed, move to the next state
                if (m_cmd_valid_d) m_state_d = TX_COMMAND;
            end
            // COMMAND: Push command onto bus
            TX_COMMAND: begin
                m_cmd_data_d  = { 1'b0, m_command_q };
                m_cmd_last_d  = 1'b0;
                m_cmd_valid_d = 1'b1;
                m_state_d     = TX_PAYLOAD;
            end
            // PAYLOAD: Push payload chunk-by-chunk onto bus
            TX_PAYLOAD: begin
                m_cmd_valid_d = 1'b0;
                for (i = 0; i < (PAYLOAD_W / BUS_W); i = (i + 1)) begin
                    if (!m_cmd_valid_d && m_valids_d[i]) begin
                        m_valids_d[i] = 1'b0;
                        m_cmd_data_d  = (m_payload_q >> (i * BUS_W));
                        m_cmd_last_d  = ~(|m_valids_d);
                        m_cmd_valid_d = 1'b1;
                    end
                end
                if (m_cmd_last_d) m_state_d = TX_TARGET;
            end
            // Catch bad state and reset to command transmit phase
            default: begin
                m_state_d  = TX_TARGET;
                m_valids_d = {(PAYLOAD_W/BUS_W){1'b0}};
            end
        endcase
    end
end

always_ff @(posedge clk, posedge rst) begin : s_transmit
    if (rst) begin
        `RESET_Q(state,               TX_TARGET);
        `RESET_Q(command,         {BUS_W{1'b0}});
        `RESET_Q(payload,     {PAYLOAD_W{1'b0}});
        `RESET_Q(valids,  {(PAYLOAD_W/8){1'b0}});
        `RESET_Q(cmd_data,        {BUS_W{1'b0}});
        `RESET_Q(cmd_last,                 1'b0);
        `RESET_Q(cmd_valid,                1'b0);
    end else begin
        `FLOP_DQ(state);
        `FLOP_DQ(command);
        `FLOP_DQ(payload);
        `FLOP_DQ(valids);
        `FLOP_DQ(cmd_data);
        `FLOP_DQ(cmd_last);
        `FLOP_DQ(cmd_valid);
    end
end

endmodule
