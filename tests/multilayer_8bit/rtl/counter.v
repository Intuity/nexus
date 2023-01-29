// Copyright 2023, Peter Birch, mailto:peter@lightlogic.co.uk
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

module counter #(
    parameter WIDTH = 32
) (
      input  wire             clk
    , input  wire             rst
    , output wire [WIDTH-1:0] count
);

reg [WIDTH-1:0] m_count;

assign count = m_count;

always @(posedge clk, posedge rst) begin : p_count
    if (rst) begin
        m_count <= {WIDTH{1'b0}};
    end else begin
        m_count <= (m_count + { {(WIDTH-1){1'b0}}, 1'b1 });
    end
end

endmodule