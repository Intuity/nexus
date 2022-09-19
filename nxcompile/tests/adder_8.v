// adder_8
// Add together the values of two 8-bit counters
//
module adder_8 (
    i_clk, i_rst,
    o_state_0_0, o_state_0_1, o_state_0_2, o_state_0_3,
    o_state_0_4, o_state_0_5, o_state_0_6, o_state_0_7,
    o_state_1_0, o_state_1_1, o_state_1_2, o_state_1_3,
    o_state_1_4, o_state_1_5, o_state_1_6, o_state_1_7,
    o_sum_state_0, o_sum_state_1, o_sum_state_2, o_sum_state_3,
    o_sum_state_4, o_sum_state_5, o_sum_state_6, o_sum_state_7
);

input  i_clk;
input  i_rst;
output o_state_0_0;
output o_state_0_1;
output o_state_0_2;
output o_state_0_3;
output o_state_0_4;
output o_state_0_5;
output o_state_0_6;
output o_state_0_7;
output o_state_1_0;
output o_state_1_1;
output o_state_1_2;
output o_state_1_3;
output o_state_1_4;
output o_state_1_5;
output o_state_1_6;
output o_state_1_7;
output o_sum_state_0;
output o_sum_state_1;
output o_sum_state_2;
output o_sum_state_3;
output o_sum_state_4;
output o_sum_state_5;
output o_sum_state_6;
output o_sum_state_7;

// =============================================================================
// Counter 0
// =============================================================================

wire [7:0] state_0_d;
wire [7:0] carry_0_d;
reg  [7:0] state_0_q;

// Bottom bit just toggles
assign state_0_d[0] = ~state_0_q[0];
assign carry_0_d[0] =  state_0_q[0];

// All other bits are half adders
assign state_0_d[1] = carry_0_d[0] ^ state_0_q[1];
assign carry_0_d[1] = carry_0_d[0] & state_0_q[1];

assign state_0_d[2] = carry_0_d[1] ^ state_0_q[2];
assign carry_0_d[2] = carry_0_d[1] & state_0_q[2];

assign state_0_d[3] = carry_0_d[2] ^ state_0_q[3];
assign carry_0_d[3] = carry_0_d[2] & state_0_q[3];

assign state_0_d[4] = carry_0_d[3] ^ state_0_q[4];
assign carry_0_d[4] = carry_0_d[3] & state_0_q[4];

assign state_0_d[5] = carry_0_d[4] ^ state_0_q[5];
assign carry_0_d[5] = carry_0_d[4] & state_0_q[5];

assign state_0_d[6] = carry_0_d[5] ^ state_0_q[6];
assign carry_0_d[6] = carry_0_d[5] & state_0_q[6];

assign state_0_d[7] = carry_0_d[6] ^ state_0_q[7];
assign carry_0_d[7] = carry_0_d[6] & state_0_q[7];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[0] <= 1'd0;
    else       state_0_q[0] <= state_0_d[0];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[1] <= 1'd0;
    else       state_0_q[1] <= state_0_d[1];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[2] <= 1'd0;
    else       state_0_q[2] <= state_0_d[2];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[3] <= 1'd0;
    else       state_0_q[3] <= state_0_d[3];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[4] <= 1'd0;
    else       state_0_q[4] <= state_0_d[4];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[5] <= 1'd0;
    else       state_0_q[5] <= state_0_d[5];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[6] <= 1'd0;
    else       state_0_q[6] <= state_0_d[6];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[7] <= 1'd0;
    else       state_0_q[7] <= state_0_d[7];

assign o_state_0_0 = state_0_q[0];
assign o_state_0_1 = state_0_q[1];
assign o_state_0_2 = state_0_q[2];
assign o_state_0_3 = state_0_q[3];
assign o_state_0_4 = state_0_q[4];
assign o_state_0_5 = state_0_q[5];
assign o_state_0_6 = state_0_q[6];
assign o_state_0_7 = state_0_q[7];

// =============================================================================
// Counter 1
// =============================================================================

wire [7:0] state_1_d;
wire [7:0] carry_1_d;
reg  [7:0] state_1_q;

// Bottom bit just toggles
assign state_1_d[0] = ~state_1_q[0];
assign carry_1_d[0] =  state_1_q[0];

// All other bits are half adders
assign state_1_d[1] = carry_1_d[0] ^ state_1_q[1];
assign carry_1_d[1] = carry_1_d[0] & state_1_q[1];

assign state_1_d[2] = carry_1_d[1] ^ state_1_q[2];
assign carry_1_d[2] = carry_1_d[1] & state_1_q[2];

assign state_1_d[3] = carry_1_d[2] ^ state_1_q[3];
assign carry_1_d[3] = carry_1_d[2] & state_1_q[3];

assign state_1_d[4] = carry_1_d[3] ^ state_1_q[4];
assign carry_1_d[4] = carry_1_d[3] & state_1_q[4];

assign state_1_d[5] = carry_1_d[4] ^ state_1_q[5];
assign carry_1_d[5] = carry_1_d[4] & state_1_q[5];

assign state_1_d[6] = carry_1_d[5] ^ state_1_q[6];
assign carry_1_d[6] = carry_1_d[5] & state_1_q[6];

assign state_1_d[7] = carry_1_d[6] ^ state_1_q[7];
assign carry_1_d[7] = carry_1_d[6] & state_1_q[7];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[0] <= 1'd0;
    else       state_1_q[0] <= state_1_d[0];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[1] <= 1'd0;
    else       state_1_q[1] <= state_1_d[1];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[2] <= 1'd0;
    else       state_1_q[2] <= state_1_d[2];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[3] <= 1'd0;
    else       state_1_q[3] <= state_1_d[3];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[4] <= 1'd0;
    else       state_1_q[4] <= state_1_d[4];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[5] <= 1'd0;
    else       state_1_q[5] <= state_1_d[5];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[6] <= 1'd0;
    else       state_1_q[6] <= state_1_d[6];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[7] <= 1'd0;
    else       state_1_q[7] <= state_1_d[7];

assign o_state_1_0 = state_1_q[0];
assign o_state_1_1 = state_1_q[1];
assign o_state_1_2 = state_1_q[2];
assign o_state_1_3 = state_1_q[3];
assign o_state_1_4 = state_1_q[4];
assign o_state_1_5 = state_1_q[5];
assign o_state_1_6 = state_1_q[6];
assign o_state_1_7 = state_1_q[7];

// =============================================================================
// Adder
// =============================================================================

wire [7:0] sum_state_d;
wire [7:0] sum_carry_d;
reg  [7:0] sum_state_q;

// LSB is a half adder
assign sum_state_d[0] = state_0_q[0] ^ state_1_q[0];
assign sum_carry_d[0] = state_0_q[0] & state_1_q[0];

// All other bits are full adders
assign sum_state_d[1] = sum_carry_d[0] ^ (state_0_q[1] ^ state_1_q[1]);
assign sum_carry_d[1] = (sum_carry_d[0] & state_0_q[1]) |
                        (sum_carry_d[0] & state_1_q[1]) |
                        (state_0_q[1]   & state_1_q[1]);

assign sum_state_d[2] = sum_carry_d[1] ^ (state_0_q[2] ^ state_1_q[2]);
assign sum_carry_d[2] = (sum_carry_d[1] & state_0_q[2]) |
                        (sum_carry_d[1] & state_1_q[2]) |
                        (state_0_q[2]   & state_1_q[2]);

assign sum_state_d[3] = sum_carry_d[2] ^ (state_0_q[3] ^ state_1_q[3]);
assign sum_carry_d[3] = (sum_carry_d[2] & state_0_q[3]) |
                        (sum_carry_d[2] & state_1_q[3]) |
                        (state_0_q[3]   & state_1_q[3]);

assign sum_state_d[4] = sum_carry_d[3] ^ (state_0_q[4] ^ state_1_q[4]);
assign sum_carry_d[4] = (sum_carry_d[3] & state_0_q[4]) |
                        (sum_carry_d[3] & state_1_q[4]) |
                        (state_0_q[4]   & state_1_q[4]);

assign sum_state_d[5] = sum_carry_d[4] ^ (state_0_q[5] ^ state_1_q[5]);
assign sum_carry_d[5] = (sum_carry_d[4] & state_0_q[5]) |
                        (sum_carry_d[4] & state_1_q[5]) |
                        (state_0_q[5]   & state_1_q[5]);

assign sum_state_d[6] = sum_carry_d[5] ^ (state_0_q[6] ^ state_1_q[6]);
assign sum_carry_d[6] = (sum_carry_d[5] & state_0_q[6]) |
                        (sum_carry_d[5] & state_1_q[6]) |
                        (state_0_q[6]   & state_1_q[6]);

assign sum_state_d[7] = sum_carry_d[6] ^ (state_0_q[7] ^ state_1_q[7]);
assign sum_carry_d[7] = (sum_carry_d[6] & state_0_q[7]) |
                        (sum_carry_d[6] & state_1_q[7]) |
                        (state_0_q[7]   & state_1_q[7]);

always @(posedge i_clk, posedge i_rst)
    if (i_rst) sum_state_q[0] <= 1'd0;
    else       sum_state_q[0] <= sum_state_d[0];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) sum_state_q[1] <= 1'd0;
    else       sum_state_q[1] <= sum_state_d[1];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) sum_state_q[2] <= 1'd0;
    else       sum_state_q[2] <= sum_state_d[2];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) sum_state_q[3] <= 1'd0;
    else       sum_state_q[3] <= sum_state_d[3];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) sum_state_q[4] <= 1'd0;
    else       sum_state_q[4] <= sum_state_d[4];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) sum_state_q[5] <= 1'd0;
    else       sum_state_q[5] <= sum_state_d[5];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) sum_state_q[6] <= 1'd0;
    else       sum_state_q[6] <= sum_state_d[6];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) sum_state_q[7] <= 1'd0;
    else       sum_state_q[7] <= sum_state_d[7];

assign o_sum_state_0 = sum_state_q[0];
assign o_sum_state_1 = sum_state_q[1];
assign o_sum_state_2 = sum_state_q[2];
assign o_sum_state_3 = sum_state_q[3];
assign o_sum_state_4 = sum_state_q[4];
assign o_sum_state_5 = sum_state_q[5];
assign o_sum_state_6 = sum_state_q[6];
assign o_sum_state_7 = sum_state_q[7];

endmodule : adder_8
