// Self-checking Verilator testbench for prim_slicer (default InW=64, OutW=8, IndexW=4).
// Reference oracle: a from-scratch byte-extraction model independent of the RTL's
// unroll-and-select implementation.
#include "Vprim_slicer.h"
#include "verilated.h"
#include <cstdint>
#include <cstdio>
#include <random>

static vluint64_t g_time = 0;
double sc_time_stamp() { return static_cast<double>(g_time); }

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  Vprim_slicer* dut = new Vprim_slicer;

  std::mt19937 rng(20261003);
  std::uniform_int_distribution<uint64_t> data_dist(0, UINT64_MAX);
  std::uniform_int_distribution<int> sel_dist(0, 15); // IndexW=4 -> sel_i in [0,15]

  int n_trials = 2000;
  int mismatches = 0;
  for (int t = 0; t < n_trials; t++) {
    uint64_t data = data_dist(rng);
    int sel = sel_dist(rng);

    dut->data_i = data;
    dut->sel_i = static_cast<uint8_t>(sel);
    dut->eval();

    // Reference: InW=64 bits zero-extended to UnrollW=128 bits, then the sel-th 8-bit chunk.
    uint8_t expected;
    if (sel * 8 < 64) {
      expected = static_cast<uint8_t>((data >> (sel * 8)) & 0xFF);
    } else {
      expected = 0; // beyond the real 64 bits, the unroll is zero-padded
    }

    if (dut->data_o != expected) {
      mismatches++;
      if (mismatches <= 5) {
        std::fprintf(stderr, "mismatch at trial %d: data=0x%016llx sel=%d rtl=0x%02x exp=0x%02x\n",
                     t, (unsigned long long)data, sel, dut->data_o, expected);
      }
    }
  }

  std::printf("prim_slicer: %d/%d trials matched the reference chunk extraction\n",
              n_trials - mismatches, n_trials);
  dut->final();
  delete dut;
  return mismatches == 0 ? 0 : 1;
}
