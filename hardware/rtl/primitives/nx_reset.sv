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

// nx_reset
// Hard and soft reset controller for Nexus
//
module nx_reset #(
    parameter RESET_LENGTH = 10 // Number of cycles to stretch the reset for
) (
      input  logic i_clk
    , input  logic i_rst_hard
    , input  logic i_rst_soft
    , output logic o_rst_internal
);

logic                    rst_combined;
logic [RESET_LENGTH-1:0] extended_q;
logic                    result_q;

// Drive reset output from the extended reset signal
assign o_rst_internal = result_q;

// Combine soft and hard reset requests
assign rst_combined = (i_rst_hard || i_rst_soft);

always_ff @(posedge i_clk, posedge rst_combined) begin : p_reset
    if (rst_combined) begin
        extended_q <= {RESET_LENGTH{1'b1}};
        result_q   <= 1'b1;
    end else begin
        extended_q <= { extended_q[RESET_LENGTH-2:0], 1'b0 };
        result_q   <= |extended_q;
    end
end

endmodule : nx_reset
