// Self-checking Verilator testbench for prim_leading_one_ppc (default N=8).
// Despite the module's name, its parallel-prefix-OR construction isolates the *lowest* set bit
// of in_i (ppc_out runs from bit 0 upward), not the highest; this testbench's reference oracle
// checks exactly that behavior, confirmed by reading the RTL rather than assumed from the name
// (see this repo's README Findings for why that distinction mattered).
#include "Vprim_leading_one_ppc.h"
#include "verilated.h"
#include <cstdint>
#include <cstdio>
#include <random>

static vluint64_t g_time = 0;
double sc_time_stamp() { return static_cast<double>(g_time); }

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  Vprim_leading_one_ppc* dut = new Vprim_leading_one_ppc;

  std::mt19937 rng(20261007);
  std::uniform_int_distribution<int> val_dist(0, 255);

  int n_trials = 2000;
  int mismatches = 0;
  for (int t = 0; t < n_trials; t++) {
    uint8_t in_i = static_cast<uint8_t>(val_dist(rng));

    dut->in_i = in_i;
    dut->eval();

    int exp_idx = -1;
    for (int i = 0; i < 8; i++) {
      if (in_i & (1u << i)) { exp_idx = i; break; }
    }
    uint8_t exp_leading_one = (exp_idx == -1) ? 0 : (1u << exp_idx);
    uint8_t exp_idx_o = (exp_idx == -1) ? 0 : static_cast<uint8_t>(exp_idx);

    bool ok = (dut->leading_one_o == exp_leading_one) && (dut->idx_o == exp_idx_o);
    if (!ok) {
      mismatches++;
      if (mismatches <= 5) {
        std::fprintf(stderr,
                     "mismatch at trial %d: in=0x%02x rtl(leading_one=0x%02x idx=%d) "
                     "exp(leading_one=0x%02x idx=%d)\n",
                     t, in_i, dut->leading_one_o, dut->idx_o, exp_leading_one, exp_idx_o);
      }
    }
  }

  std::printf("prim_leading_one_ppc: %d/%d trials matched the reference lowest-set-bit model\n",
              n_trials - mismatches, n_trials);
  dut->final();
  delete dut;
  return mismatches == 0 ? 0 : 1;
}
