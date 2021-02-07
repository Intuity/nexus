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