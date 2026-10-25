// Self-checking Verilator testbench for prim_onehot_enc (default OneHotWidth=32, InputWidth=5).
// Reference oracle: out_o == en_i ? (1 << in_i) : 0, independent of the RTL's per-bit compare.
#include "Vprim_onehot_enc.h"
#include "verilated.h"
#include <cstdint>
#include <cstdio>
#include <random>

static vluint64_t g_time = 0;
double sc_time_stamp() { return static_cast<double>(g_time); }

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  Vprim_onehot_enc* dut = new Vprim_onehot_enc;

  std::mt19937 rng(20261009);
  std::uniform_int_distribution<int> in_dist(0, 31);
  std::uniform_int_distribution<int> en_dist(0, 1);

  int n_trials = 2000;
  int mismatches = 0;
  for (int t = 0; t < n_trials; t++) {
    int in_i = in_dist(rng);
    int en_i = en_dist(rng);

    dut->in_i = in_i;
    dut->en_i = en_i;
    dut->eval();

    uint32_t expected = en_i ? (1u << in_i) : 0u;

    if (dut->out_o != expected) {
      mismatches++;
      if (mismatches <= 5) {
        std::fprintf(stderr, "mismatch at trial %d: in=%d en=%d rtl=0x%08x exp=0x%08x\n", t, in_i,
                     en_i, dut->out_o, expected);
      }
    }
  }

  std::printf("prim_onehot_enc: %d/%d trials matched the reference bit-select model\n",
              n_trials - mismatches, n_trials);
  dut->final();
  delete dut;
  return mismatches == 0 ? 0 : 1;
}
