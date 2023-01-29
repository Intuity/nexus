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

module Top #(
    parameter WIDTH = 32
) (
      input  wire             clk
    , input  wire             rst
    , output wire [WIDTH-1:0] sum
    , output wire             overflow
);

wire [WIDTH-1:0] m_count_val_a, m_count_val_b;

counter #(
    .WIDTH(WIDTH)
) m_counter_a (
      .clk  (clk          )
    , .rst  (rst          )
    , .count(m_count_val_a)
);

counter #(
    .WIDTH(WIDTH)
) m_counter_b (
      .clk  (clk          )
    , .rst  (rst          )
    , .count(m_count_val_b)
);

adder #(
    .WIDTH(WIDTH)
) m_adder (
      .clk     (clk          )
    , .rst     (rst          )
    , .value_a (m_count_val_a)
    , .value_b (m_count_val_b)
    , .sum     (sum          )
    , .overflow(overflow     )
);

endmodule
