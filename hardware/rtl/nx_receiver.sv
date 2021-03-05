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

module nx_receiver #(
      parameter TARGET_W  =  8
    , parameter BUS_W     =  8
    , parameter PAYLOAD_W = 24
) (
      input  logic                         clk
    , input  logic                         rst
    // Command interface
    , input  logic [            BUS_W-1:0] cmd_data
    , input  logic                         cmd_last
    , input  logic                         cmd_valid
    , output logic                         cmd_ready
    // Data received
    , output logic [            BUS_W-1:0] rx_command
    , output logic [        PAYLOAD_W-1:0] rx_payload
    , output logic [(PAYLOAD_W/BUS_W)-1:0] rx_valid
    , output logic                         rx_complete
    , input  logic                         rx_ready
);

localparam FULL_W    = TARGET_W + BUS_W + PAYLOAD_W; // { TGT, CMD, PAYLOAD }
localparam VALID_W   = PAYLOAD_W / BUS_W;
localparam MAX_CYCLE = (FULL_W + (BUS_W - 1)) / BUS_W;
localparam COUNT_W   = $clog2(MAX_CYCLE);

logic [COUNT_W-1:0] `DECLARE_DQ(cycle,    clk, rst, {COUNT_W{1'b0}})
logic [ FULL_W-1:0] `DECLARE_DQ(accum,    clk, rst, {FULL_W{1'b0}} )
logic [VALID_W-1:0] `DECLARE_DQ(valid,    clk, rst, {VALID_W{1'b0}})
logic               `DECLARE_DQ(complete, clk, rst, 1'b0           )

assign cmd_ready   = rx_ready;
assign rx_command  = m_accum_q[FULL_W-1:FULL_W-BUS_W];
assign rx_payload  = m_accum_q[FULL_W-BUS_W-1:0];
assign rx_valid    = m_valid_q;
assign rx_complete = m_complete_q;

always_comb begin : c_receive
    `INIT_D(cycle);
    `INIT_D(accum);
    `INIT_D(valid);
    `INIT_D(complete);

    if (rx_ready) begin
        case (m_cycle_d)
            // Cycle 0: Ignore the target ID on the front of the packet
            0: begin
                m_valid_d    = 1'b0;
                m_accum_d    = {FULL_W{1'b0}};
                m_complete_d = 1'b0;
            end
            // Cycle 1: Receive the command, still hold valid low
            1: begin
                m_accum_d[FULL_W-1:FULL_W-BUS_W] = cmd_data;
                m_valid_d                        = 1'b0;
            end
            // Cycle 2+: Insert new data, flag valid when last tick received
            default: begin
                m_accum_d[FULL_W-BUS_W-1:0] = {
                    m_accum_d[FULL_W-(BUS_W*2)-1:0], cmd_data
                };
                m_valid_d    = { m_valid_d[VALID_W-2:0], 1'b1 };
                m_complete_d = cmd_last;
            end
        endcase
        // Advance counter if data was presented
        if (cmd_valid && cmd_ready) begin
            if (cmd_last) begin
                m_cycle_d = {COUNT_W{1'b0}};
            end else begin
                m_cycle_d = (m_cycle_d + { {(COUNT_W-1){1'b0}}, 1'b1 });
            end
        end
    end
end

endmodule
