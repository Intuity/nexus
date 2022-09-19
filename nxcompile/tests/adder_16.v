// adder_16
// Add together the values of two 8-bit counters
//
module adder_16 (
    i_clk, i_rst,
    o_state_0_0, o_state_0_1, o_state_0_2, o_state_0_3,
    o_state_0_4, o_state_0_5, o_state_0_6, o_state_0_7,
    o_state_0_8, o_state_0_9, o_state_0_10, o_state_0_11,
    o_state_0_12, o_state_0_13, o_state_0_14, o_state_0_15,
    o_state_1_0, o_state_1_1, o_state_1_2, o_state_1_3,
    o_state_1_4, o_state_1_5, o_state_1_6, o_state_1_7,
    o_state_1_8, o_state_1_9, o_state_1_10, o_state_1_11,
    o_state_1_12, o_state_1_13, o_state_1_14, o_state_1_15,
    o_sum_state_0, o_sum_state_1, o_sum_state_2, o_sum_state_3,
    o_sum_state_4, o_sum_state_5, o_sum_state_6, o_sum_state_7,
    o_sum_state_8, o_sum_state_9, o_sum_state_10, o_sum_state_11,
    o_sum_state_12, o_sum_state_13, o_sum_state_14, o_sum_state_15
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
output o_state_0_8;
output o_state_0_9;
output o_state_0_10;
output o_state_0_11;
output o_state_0_12;
output o_state_0_13;
output o_state_0_14;
output o_state_0_15;
output o_state_1_0;
output o_state_1_1;
output o_state_1_2;
output o_state_1_3;
output o_state_1_4;
output o_state_1_5;
output o_state_1_6;
output o_state_1_7;
output o_state_1_8;
output o_state_1_9;
output o_state_1_10;
output o_state_1_11;
output o_state_1_12;
output o_state_1_13;
output o_state_1_14;
output o_state_1_15;
output o_sum_state_0;
output o_sum_state_1;
output o_sum_state_2;
output o_sum_state_3;
output o_sum_state_4;
output o_sum_state_5;
output o_sum_state_6;
output o_sum_state_7;
output o_sum_state_8;
output o_sum_state_9;
output o_sum_state_10;
output o_sum_state_11;
output o_sum_state_12;
output o_sum_state_13;
output o_sum_state_14;
output o_sum_state_15;

// =============================================================================
// Counter 0
// =============================================================================

wire [15:0] state_0_d;
wire [15:0] carry_0_d;
reg  [15:0] state_0_q;

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

assign state_0_d[8] = carry_0_d[7] ^ state_0_q[8];
assign carry_0_d[8] = carry_0_d[7] & state_0_q[8];

assign state_0_d[9] = carry_0_d[8] ^ state_0_q[9];
assign carry_0_d[9] = carry_0_d[8] & state_0_q[9];

assign state_0_d[10] = carry_0_d[9] ^ state_0_q[10];
assign carry_0_d[10] = carry_0_d[9] & state_0_q[10];

assign state_0_d[11] = carry_0_d[10] ^ state_0_q[11];
assign carry_0_d[11] = carry_0_d[10] & state_0_q[11];

assign state_0_d[12] = carry_0_d[11] ^ state_0_q[12];
assign carry_0_d[12] = carry_0_d[11] & state_0_q[12];

assign state_0_d[13] = carry_0_d[12] ^ state_0_q[13];
assign carry_0_d[13] = carry_0_d[12] & state_0_q[13];

assign state_0_d[14] = carry_0_d[13] ^ state_0_q[14];
assign carry_0_d[14] = carry_0_d[13] & state_0_q[14];

assign state_0_d[15] = carry_0_d[14] ^ state_0_q[15];
assign carry_0_d[15] = carry_0_d[14] & state_0_q[15];

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

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[8] <= 1'd0;
    else       state_0_q[8] <= state_0_d[8];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[9] <= 1'd0;
    else       state_0_q[9] <= state_0_d[9];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[10] <= 1'd0;
    else       state_0_q[10] <= state_0_d[10];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[11] <= 1'd0;
    else       state_0_q[11] <= state_0_d[11];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[12] <= 1'd0;
    else       state_0_q[12] <= state_0_d[12];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[13] <= 1'd0;
    else       state_0_q[13] <= state_0_d[13];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[14] <= 1'd0;
    else       state_0_q[14] <= state_0_d[14];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_0_q[15] <= 1'd0;
    else       state_0_q[15] <= state_0_d[15];

assign o_state_0_0 = state_0_q[0];
assign o_state_0_1 = state_0_q[1];
assign o_state_0_2 = state_0_q[2];
assign o_state_0_3 = state_0_q[3];
assign o_state_0_4 = state_0_q[4];
assign o_state_0_5 = state_0_q[5];
assign o_state_0_6 = state_0_q[6];
assign o_state_0_7 = state_0_q[7];
assign o_state_0_8 = state_0_q[8];
assign o_state_0_9 = state_0_q[9];
assign o_state_0_10 = state_0_q[10];
assign o_state_0_11 = state_0_q[11];
assign o_state_0_12 = state_0_q[12];
assign o_state_0_13 = state_0_q[13];
assign o_state_0_14 = state_0_q[14];
assign o_state_0_15 = state_0_q[15];

// =============================================================================
// Counter 1
// =============================================================================

wire [15:0] state_1_d;
wire [15:0] carry_1_d;
reg  [15:0] state_1_q;

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

assign state_1_d[8] = carry_1_d[7] ^ state_1_q[8];
assign carry_1_d[8] = carry_1_d[7] & state_1_q[8];

assign state_1_d[9] = carry_1_d[8] ^ state_1_q[9];
assign carry_1_d[9] = carry_1_d[8] & state_1_q[9];

assign state_1_d[10] = carry_1_d[9] ^ state_1_q[10];
assign carry_1_d[10] = carry_1_d[9] & state_1_q[10];

assign state_1_d[11] = carry_1_d[10] ^ state_1_q[11];
assign carry_1_d[11] = carry_1_d[10] & state_1_q[11];

assign state_1_d[12] = carry_1_d[11] ^ state_1_q[12];
assign carry_1_d[12] = carry_1_d[11] & state_1_q[12];

assign state_1_d[13] = carry_1_d[12] ^ state_1_q[13];
assign carry_1_d[13] = carry_1_d[12] & state_1_q[13];

assign state_1_d[14] = carry_1_d[13] ^ state_1_q[14];
assign carry_1_d[14] = carry_1_d[13] & state_1_q[14];

assign state_1_d[15] = carry_1_d[14] ^ state_1_q[15];
assign carry_1_d[15] = carry_1_d[14] & state_1_q[15];

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

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[8] <= 1'd0;
    else       state_1_q[8] <= state_1_d[8];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[9] <= 1'd0;
    else       state_1_q[9] <= state_1_d[9];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[10] <= 1'd0;
    else       state_1_q[10] <= state_1_d[10];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[11] <= 1'd0;
    else       state_1_q[11] <= state_1_d[11];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[12] <= 1'd0;
    else       state_1_q[12] <= state_1_d[12];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[13] <= 1'd0;
    else       state_1_q[13] <= state_1_d[13];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[14] <= 1'd0;
    else       state_1_q[14] <= state_1_d[14];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_1_q[15] <= 1'd0;
    else       state_1_q[15] <= state_1_d[15];

assign o_state_1_0 = state_1_q[0];
assign o_state_1_1 = state_1_q[1];
assign o_state_1_2 = state_1_q[2];
assign o_state_1_3 = state_1_q[3];
assign o_state_1_4 = state_1_q[4];
assign o_state_1_5 = state_1_q[5];
assign o_state_1_6 = state_1_q[6];
assign o_state_1_7 = state_1_q[7];
assign o_state_1_8 = state_1_q[8];
assign o_state_1_9 = state_1_q[9];
assign o_state_1_10 = state_1_q[10];
assign o_state_1_11 = state_1_q[11];
assign o_state_1_12 = state_1_q[12];
assign o_state_1_13 = state_1_q[13];
assign o_state_1_14 = state_1_q[14];
assign o_state_1_15 = state_1_q[15];

// =============================================================================
// Adder
// =============================================================================

wire [15:0] sum_state_d;
wire [15:0] sum_carry_d;
reg  [15:0] sum_state_q;

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

assign sum_state_d[8] = sum_carry_d[7] ^ (state_0_q[8] ^ state_1_q[8]);
assign sum_carry_d[8] = (sum_carry_d[7] & state_0_q[8]) |
                        (sum_carry_d[7] & state_1_q[8]) |
                        (state_0_q[8]   & state_1_q[8]);

assign sum_state_d[9] = sum_carry_d[8] ^ (state_0_q[9] ^ state_1_q[9]);
assign sum_carry_d[9] = (sum_carry_d[8] & state_0_q[9]) |
                        (sum_carry_d[8] & state_1_q[9]) |
                        (state_0_q[9]   & state_1_q[9]);

assign sum_state_d[10] = sum_carry_d[9] ^ (state_0_q[10] ^ state_1_q[10]);
assign sum_carry_d[10] = (sum_carry_d[9] & state_0_q[10]) |
                        (sum_carry_d[9] & state_1_q[10]) |
                        (state_0_q[10]   & state_1_q[10]);

assign sum_state_d[11] = sum_carry_d[10] ^ (state_0_q[11] ^ state_1_q[11]);
assign sum_carry_d[11] = (sum_carry_d[10] & state_0_q[11]) |
                        (sum_carry_d[10] & state_1_q[11]) |
                        (state_0_q[11]   & state_1_q[11]);

assign sum_state_d[12] = sum_carry_d[11] ^ (state_0_q[12] ^ state_1_q[12]);
assign sum_carry_d[12] = (sum_carry_d[11] & state_0_q[12]) |
                        (sum_carry_d[11] & state_1_q[12]) |
                        (state_0_q[12]   & state_1_q[12]);

assign sum_state_d[13] = sum_carry_d[12] ^ (state_0_q[13] ^ state_1_q[13]);
assign sum_carry_d[13] = (sum_carry_d[12] & state_0_q[13]) |
                        (sum_carry_d[12] & state_1_q[13]) |
                        (state_0_q[13]   & state_1_q[13]);

assign sum_state_d[14] = sum_carry_d[13] ^ (state_0_q[14] ^ state_1_q[14]);
assign sum_carry_d[14] = (sum_carry_d[13] & state_0_q[14]) |
                        (sum_carry_d[13] & state_1_q[14]) |
                        (state_0_q[14]   & state_1_q[14]);

assign sum_state_d[15] = sum_carry_d[14] ^ (state_0_q[15] ^ state_1_q[15]);
assign sum_carry_d[15] = (sum_carry_d[14] & state_0_q[15]) |
                        (sum_carry_d[14] & state_1_q[15]) |
                        (state_0_q[15]   & state_1_q[15]);

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

endmodule : adder_16
