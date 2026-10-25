// Self-checking Verilator testbench for prim_onehot_check, built with -GAddrCheck=1'b0
// -GEnableCheck=1'b0 so only the onehot0 structural check is exercised (addr_i, en_i unused).
// Reference oracle: popcount(oh_i) > 1, independent of the RTL's binary-tree conflict detector.
#include "Vprim_onehot_check.h"
#include "verilated.h"
#include <bitset>
#include <cstdint>
#include <cstdio>
#include <random>

static vluint64_t g_time = 0;
double sc_time_stamp() { return static_cast<double>(g_time); }

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  Vprim_onehot_check* dut = new Vprim_onehot_check;

  std::mt19937 rng(20261006);
  std::uniform_int_distribution<uint32_t> full_dist(0, 0xFFFFFFFFu);
  std::uniform_int_distribution<int> bitpos_dist(0, 31);

  dut->clk_i = 0;
  dut->rst_ni = 1;
  dut->addr_i = 0;
  dut->en_i = 0;

  int n_trials = 4000;
  int mismatches = 0;
  for (int t = 0; t < n_trials; t++) {
    uint32_t oh;
    // Mix: a third exactly one-hot, a third zero, a third arbitrary (usually multi-bit).
    int mode = t % 3;
    if (mode == 0) {
      oh = 1u << bitpos_dist(rng);
    } else if (mode == 1) {
      oh = 0;
    } else {
      oh = full_dist(rng);
    }

    dut->oh_i = oh;
    dut->eval();

    int popcount = std::bitset<32>(oh).count();
    bool exp_err = popcount > 1;

    if (static_cast<bool>(dut->err_o) != exp_err) {
      mismatches++;
      if (mismatches <= 5) {
        std::fprintf(stderr, "mismatch at trial %d: oh=0x%08x popcount=%d rtl_err=%d exp_err=%d\n",
                     t, oh, popcount, dut->err_o, exp_err);
      }
    }
  }

  std::printf("prim_onehot_check: %d/%d trials matched the reference popcount check\n",
              n_trials - mismatches, n_trials);
  dut->final();
  delete dut;
  return mismatches == 0 ? 0 : 1;
}
