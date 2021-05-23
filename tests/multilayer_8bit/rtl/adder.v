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

module adder #(
    parameter WIDTH = 32
) (
      input  wire             clk
    , input  wire             rst
    , input  wire [WIDTH-1:0] value_a
    , input  wire [WIDTH-1:0] value_b
    , output wire [WIDTH-1:0] sum
    , output wire             overflow
);

reg [WIDTH:0] m_result;

assign {overflow, sum} = m_result;

always @(posedge clk, posedge rst) begin
    if (rst) begin
        m_result <= {WIDTH{1'b0}};
    end else begin
        m_result <= value_a + value_b;
    end
end

endmodule
