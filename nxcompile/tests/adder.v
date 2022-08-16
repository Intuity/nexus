// adder
// Add together the values of two counters
//
module adder (
    i_clk, i_rst,
    o_state_0_0, o_state_0_1, o_state_0_2, o_state_0_3,
    o_state_1_0, o_state_1_1, o_state_1_2, o_state_1_3,
    o_sum_state_0, o_sum_state_1, o_sum_state_2, o_sum_state_3
);

input  i_clk;
input  i_rst;
output o_state_0_0;
output o_state_0_1;
output o_state_0_2;
output o_state_0_3;
output o_state_1_0;
output o_state_1_1;
output o_state_1_2;
output o_state_1_3;
output o_sum_state_0;
output o_sum_state_1;
output o_sum_state_2;
output o_sum_state_3;

// =============================================================================
// Counter 0
// =============================================================================

wire [3:0] state_0_d;
wire [3:0] carry_0_d;
reg  [3:0] state_0_q;

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

assign o_state_0_0 = state_0_q[0];
assign o_state_0_1 = state_0_q[1];
assign o_state_0_2 = state_0_q[2];
assign o_state_0_3 = state_0_q[3];

// =============================================================================
// Counter 1
// =============================================================================

wire [3:0] state_1_d;
wire [3:0] carry_1_d;
reg  [3:0] state_1_q;

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

assign o_state_1_0 = state_1_q[0];
assign o_state_1_1 = state_1_q[1];
assign o_state_1_2 = state_1_q[2];
assign o_state_1_3 = state_1_q[3];

// =============================================================================
// Adder
// =============================================================================

wire [4:0] sum_state_d;
wire [4:0] sum_carry_d;
reg  [3:0] sum_state_q;

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

assign o_sum_state_0 = sum_state_q[0];
assign o_sum_state_1 = sum_state_q[1];
assign o_sum_state_2 = sum_state_q[2];
assign o_sum_state_3 = sum_state_q[3];

endmodule : adder
