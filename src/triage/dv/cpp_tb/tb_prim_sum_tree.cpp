// Self-checking Verilator testbench for prim_sum_tree, built with -GNumSrc=4 -GInWidth=8
// -GSaturate=1'b0 (so OutWidth = InWidth + log2(NumSrc) = 10 bits, no overflow possible).
// Reference oracle: a from-scratch sum over indices where valid_i is set, independent of the
// RTL's binary-tree reduction.
#include "Vprim_sum_tree.h"
#include "verilated.h"
#include <cstdint>
#include <cstdio>
#include <random>

static vluint64_t g_time = 0;
double sc_time_stamp() { return static_cast<double>(g_time); }

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  Vprim_sum_tree* dut = new Vprim_sum_tree;

  std::mt19937 rng(20261005);
  std::uniform_int_distribution<int> val_dist(0, 255);
  std::uniform_int_distribution<int> bit_dist(0, 1);

  dut->clk_i = 0;
  dut->rst_ni = 1;

  int n_trials = 4000;
  int mismatches = 0;
  for (int t = 0; t < n_trials; t++) {
    uint8_t values[4];
    uint8_t valid = 0;
    for (int i = 0; i < 4; i++) {
      values[i] = static_cast<uint8_t>(val_dist(rng));
      if (bit_dist(rng)) valid |= (1u << i);
    }

    uint32_t values_i = 0;
    for (int i = 0; i < 4; i++) values_i |= (static_cast<uint32_t>(values[i]) << (i * 8));

    dut->values_i = values_i;
    dut->valid_i = valid;
    dut->eval();

    bool any_valid = valid != 0;
    uint32_t exp_sum = 0;
    for (int i = 0; i < 4; i++) {
      if (valid & (1u << i)) exp_sum += values[i];
    }

    bool ok = (static_cast<bool>(dut->sum_valid_o) == any_valid) &&
              (dut->sum_value_o == static_cast<uint16_t>(exp_sum));
    if (!ok) {
      mismatches++;
      if (mismatches <= 5) {
        std::fprintf(stderr,
                     "mismatch at trial %d: values=[%d,%d,%d,%d] valid=0x%x -> rtl(sum=%d "
                     "valid=%d) exp(sum=%d valid=%d)\n",
                     t, values[0], values[1], values[2], values[3], valid, dut->sum_value_o,
                     dut->sum_valid_o, exp_sum, any_valid);
      }
    }
  }

  std::printf("prim_sum_tree: %d/%d trials matched the reference sum-of-valid scan\n",
              n_trials - mismatches, n_trials);
  dut->final();
  delete dut;
  return mismatches == 0 ? 0 : 1;
}
