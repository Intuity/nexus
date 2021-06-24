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

// nx_stream_skid
// Parameterisable stream skid buffer
//
module nx_stream_skid #(
    parameter STREAM_WIDTH = 32
) (
      input  logic                    clk_i
    , input  logic                    rst_i
    // Inbound message stream
    , input  logic [STREAM_WIDTH-1:0] inbound_data_i
    , input  logic                    inbound_valid_i
    , output logic                    inbound_ready_o
    // Outbound message stream
    , output logic [STREAM_WIDTH-1:0] outbound_data_o
    , output logic                    outbound_valid_o
    , input  logic                    outbound_ready_i
);

logic [STREAM_WIDTH-1:0] buffer;
logic                    buffer_valid;

assign outbound_data_o  = buffer_valid ? buffer : inbound_data_i;
assign outbound_valid_o = buffer_valid || inbound_valid_i;
assign inbound_ready_o  = outbound_ready_i || !buffer_valid;

always_ff @(posedge clk_i, posedge rst_i) begin : p_skid
    if (rst_i) begin
        buffer       <= {STREAM_WIDTH{1'b0}};
        buffer_valid <= 1'b0;
    end else begin
        // Refill buffer where...
        if (
            ( buffer_valid &&  outbound_ready_i) || // It has been decanted
            (!buffer_valid && !outbound_ready_i)    // It is empty and outbound is blocking
        ) begin
            buffer       <= inbound_data_i;
            buffer_valid <= inbound_valid_i;
        end
    end
end

endmodule : nx_stream_skid
