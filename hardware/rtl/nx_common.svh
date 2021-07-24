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

// DECLARE_DQT(T, X, C, R, I)
// Declares a typed combinatorial-sequential logic pair, and sets up the
// sequential logic portion.
// Args:
//  T: Type of the signal
//  X: Name of the signal
//  C: Clock signal driving sequential logic
//  R: Reset signal driving sequential logic
//  I: Initial value for the signal to take
//
`define DECLARE_DQT(T, X, C, R, I) \
    T X, ``X``_q; \
    always_ff @(posedge C, posedge R) begin : s_``X \
        if (R) begin \
            ``X``_q <= (I); \
        end else begin \
            ``X``_q <= X; \
        end \
    end

// DECLARE_DQ(W, X, C, R, I)
// Declares a combinatorial-sequential logic pair, and sets up the sequential
// logic portion.
// Args:
//  W: Width of the signal
//  X: Name of the signal
//  C: Clock signal driving sequential logic
//  R: Reset signal driving sequential logic
//  I: Initial value for the signal to take
//
`define DECLARE_DQ(W, X, C, R, I) `DECLARE_DQT(logic [W-1:0], X, C, R, I)

// DECLARE_DQT_ARRAY(T, N, X, C, R, I)
// Declares a combinatorial-sequential logic pair for an array, and sets up the
// sequential logic portion.
// Args:
//  T: Type of the signal
//  N: Number of elements in the array
//  X: Name of the signal
//  C: Clock signal driving sequential logic
//  R: Reset signal driving sequential logic
//  I: Initial value for each signal to take
//
`define DECLARE_DQT_ARRAY(T, N, X, C, R, I) \
    T ``X`` [N-1:0], ``X``_q [N-1:0]; \
    localparam ARRAY_SIZE_``X`` = N; \
    always_ff @(posedge C, posedge R) begin : s_``X \
        int i; \
        if (R) begin \
            for (i = 0; i < N; i = (i + 1)) ``X``_q[i] <= (I); \
        end else begin \
            for (i = 0; i < N; i = (i + 1)) ``X``_q[i] <= X[i]; \
        end \
    end

// DECLARE_DQ_ARRAY(W, N, X, C, R, I)
// Declares a combinatorial-sequential logic pair for an array, and sets up the
// sequential logic portion.
// Args:
//  W: Width of the signal
//  N: Number of elements in the array
//  X: Name of the signal
//  C: Clock signal driving sequential logic
//  R: Reset signal driving sequential logic
//  I: Initial value for each signal to take
//
`define DECLARE_DQ_ARRAY(W, N, X, C, R, I) \
    `DECLARE_DQT_ARRAY(logic [W-1:0], N, X, C, R, I)

// INIT_D(X)
// Copy the sequential value back to the combinatorial value, ready for
// computing the next state.
// Args:
//  X: Name of the signal
//
`define INIT_D(X) X = ``X``_q

// INIT_D_ARRAY(X)
// Copy the sequential arrayed values back to the combinatorial arrayed values,
// ready for computing the state state.
// Args:
//  X: Name of the signal
//
`define INIT_D_ARRAY(X) \
    for (int _i = 0; _i < ARRAY_SIZE_``X``; _i = (_i + 1)) X[_i] = ``X``_q[_i]

`endif // __NX_COMMON_SVH__
