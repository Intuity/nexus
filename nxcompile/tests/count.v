// count
// Increment a count on every cycle, wrapping back to zero when the counter
// overflows
//
module count (i_clk, i_rst, o_state_0, o_state_1, o_state_2, o_state_3);

input  i_clk;
input  i_rst;
output o_state_0;
output o_state_1;
output o_state_2;
output o_state_3;

wire [3:0] state_d;
wire [3:0] carry_d;
reg  [3:0] state_q;

// Bottom bit just toggles
assign state_d[0] = ~state_q[0];
assign carry_d[0] =  state_q[0];

// All other bits are half adders
assign state_d[1] = carry_d[0] ^ state_q[1];
assign carry_d[1] = carry_d[0] & state_q[1];

assign state_d[2] = carry_d[1] ^ state_q[2];
assign carry_d[2] = carry_d[1] & state_q[2];

assign state_d[3] = carry_d[2] ^ state_q[3];
assign carry_d[3] = carry_d[2] & state_q[3];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_q[0] <= 1'd0;
    else       state_q[0] <= state_d[0];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_q[1] <= 1'd0;
    else       state_q[1] <= state_d[1];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_q[2] <= 1'd0;
    else       state_q[2] <= state_d[2];

always @(posedge i_clk, posedge i_rst)
    if (i_rst) state_q[3] <= 1'd0;
    else       state_q[3] <= state_d[3];

assign o_state_0 = state_q[0];
assign o_state_1 = state_q[1];
assign o_state_2 = state_q[2];
assign o_state_3 = state_q[3];

endmodule : count
