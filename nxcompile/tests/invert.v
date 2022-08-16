// simple
// Toggles a single bit between its two states
//
module simple (i_clk, i_rst, o_state);

input  i_clk;
input  i_rst;
output o_state;

wire state_d;
reg  state_q;

assign state_d = ~state_q;

always @(posedge i_clk, posedge i_rst)
    if (i_rst)
        state_q <= 1'd0;
    else
        state_q <= state_d;

assign o_state = state_q;

endmodule : simple
