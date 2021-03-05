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

`ifndef __NX_COMMON_SVH__
`define __NX_COMMON_SVH__

// DECLARE_DQ(X, C, R, I)
// Declares a combinatorial-sequential logic pair, and sets up the sequential
// logic portion.
// Args:
//  X: Name of the signal
//  C: Clock signal driving sequential logic
//  R: Reset signal driving sequential logic
//  I: Initial value for the signal to take
//
`define DECLARE_DQ(X, C, R, I) \
    m_``X``_d, m_``X``_q; \
    always_ff @(posedge C, posedge R) begin : s_``X \
        if (R) begin \
            m_``X``_q <= (I); \
        end else begin \
            m_``X``_q <= m_``X``_d; \
        end \
    end

// INIT_D(X)
// Copy the sequential value back to the combinatorial value, ready for
// computing the next state.
// Args:
//  X: Name of the signal
//
`define INIT_D(X) m_``X``_d = m_``X``_q

`endif // __NX_COMMON_SVH__
