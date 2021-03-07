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

module nx_arbiter #(
    parameter BUS_W = 8
) (
      input  logic             clk
    , input  logic             rst
    // Inbound interface A
    , input  logic [BUS_W-1:0] inbound_a_data
    , input  logic             inbound_a_last
    , input  logic             inbound_a_valid
    , output logic             inbound_a_ready
    // Inbound interface B
    , input  logic [BUS_W-1:0] inbound_b_data
    , input  logic             inbound_b_last
    , input  logic             inbound_b_valid
    , output logic             inbound_b_ready
    // Outbound interface
    , output logic [BUS_W-1:0] outbound_data
    , output logic             outbound_last
    , output logic             outbound_valid
    , input  logic             outbound_ready
);

logic m_active, m_lock;

logic m_source;
assign m_source = (
    // When locked to a channel, only source data from that channel
    m_lock ? ((m_active                    ) ? 1'b1 : 1'b0)
    // When not locked, prefer to alternate channel unless other isn't busy
           : (((m_active && inbound_a_valid) || ~inbound_b_valid) ? 1'b0 : 1'b1)
);

// Mux data, last, and valid onto outbound signals
assign outbound_data  = m_source ? inbound_b_data : inbound_a_data;
assign outbound_last  = m_source ? inbound_b_last : inbound_a_last;
assign outbound_valid = m_source ? inbound_b_valid : inbound_a_valid;

// Pass ready back to the active source
assign inbound_a_ready = outbound_ready & ~m_source;
assign inbound_b_ready = outbound_ready &  m_source;

// Manage channel locking
always_ff @(posedge clk, posedge rst) begin : p_lock
    if (rst) begin
        m_active <= 1'b0;
        m_lock   <= 1'b0;
    end else if (outbound_valid && outbound_ready) begin
        m_active <= m_source;
        m_lock   <= ~outbound_last;
    end
end

endmodule
