// Copyright lowRISC contributors (OpenTitan project).
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

// One-hot encoder
// Outputs a one-hot encoded version of an integer input.

module prim_onehot_enc #(
  parameter int unsigned OneHotWidth = 32,
  localparam int unsigned InputWidth = $clog2(OneHotWidth)
) (
  input  logic [InputWidth-1:0]  in_i,
  input  logic                   en_i, // out_o == '0 when en_i == 0

  output logic [OneHotWidth-1:0] out_o
);

  // BUG: changed the per-bit AND to an OR. Every bit of out_o is now 1 whenever en_i is 1,
  // regardless of in_i, instead of only the single bit matching in_i; the module still
  // correctly outputs all-zero when en_i is 0.
  for (genvar i = 0; i < OneHotWidth; ++i) begin : g_out
    assign out_o[i] = (in_i == i) | en_i;
  end
endmodule
