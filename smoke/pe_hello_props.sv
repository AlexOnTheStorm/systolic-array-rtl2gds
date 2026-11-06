// SBY "hello": after clear (with reset deasserted) the PE accumulator is zero.
module pe_hello_props (
    input logic       clk,
    input logic       rst_n,
    input logic       clear,
    input logic       en,
    input logic [7:0] a_in,
    input logic [7:0] b_in
);
  logic signed [7:0]  a_out, b_out;
  logic signed [31:0] acc;

  pe #(.DATA_WIDTH(8), .ACC_WIDTH(32)) dut (
      .clk, .rst_n, .clear, .en, .a_in, .b_in, .a_out, .b_out, .acc);

  logic past_valid = 1'b0;
  always_ff @(posedge clk) past_valid <= 1'b1;

  always_comb if (!past_valid) assume (!rst_n);   // start from reset

  always_ff @(posedge clk)
    if (past_valid && $past(rst_n) && $past(clear))
      assert (acc == 0 && a_out == 0 && b_out == 0);
endmodule
