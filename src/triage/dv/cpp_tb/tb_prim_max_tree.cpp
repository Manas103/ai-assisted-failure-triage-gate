// Self-checking Verilator testbench for prim_max_tree, built with -GNumSrc=4 -GWidth=8.
// Reference oracle: a from-scratch linear scan for the maximum valid value (ties broken by
// lowest index), independent of the RTL's binary-tree reduction.
#include "Vprim_max_tree.h"
#include "verilated.h"
#include <cstdint>
#include <cstdio>
#include <random>

static vluint64_t g_time = 0;
double sc_time_stamp() { return static_cast<double>(g_time); }

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  Vprim_max_tree* dut = new Vprim_max_tree;

  std::mt19937 rng(20261004);
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
    uint8_t exp_value;
    int exp_idx;
    if (any_valid) {
      exp_value = 0;
      exp_idx = -1;
      for (int i = 0; i < 4; i++) {
        // exp_idx == -1 picks up the first valid entry regardless of its value (a valid 0
        // must still win over "no entry chosen yet"); after that, only a strictly larger
        // value takes over, which is what keeps ties resolved to the lowest index.
        if ((valid & (1u << i)) && (exp_idx == -1 || values[i] > exp_value)) {
          exp_value = values[i];
          exp_idx = i;
        }
      }
    } else {
      exp_value = values[0];
      exp_idx = 0;
    }

    bool ok = (static_cast<bool>(dut->max_valid_o) == any_valid) &&
              (dut->max_value_o == exp_value) && (dut->max_idx_o == static_cast<uint8_t>(exp_idx));
    if (!ok) {
      mismatches++;
      if (mismatches <= 5) {
        std::fprintf(stderr,
                     "mismatch at trial %d: values=[%d,%d,%d,%d] valid=0x%x -> rtl(value=%d "
                     "idx=%d valid=%d) exp(value=%d idx=%d valid=%d)\n",
                     t, values[0], values[1], values[2], values[3], valid, dut->max_value_o,
                     dut->max_idx_o, dut->max_valid_o, exp_value, exp_idx, any_valid);
      }
    }
  }

  std::printf("prim_max_tree: %d/%d trials matched the reference max-of-valid scan\n",
              n_trials - mismatches, n_trials);
  dut->final();
  delete dut;
  return mismatches == 0 ? 0 : 1;
}
