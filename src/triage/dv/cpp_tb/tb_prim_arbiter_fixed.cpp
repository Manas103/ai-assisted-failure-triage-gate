// Self-checking Verilator testbench for prim_arbiter_fixed (default N=8, DW=32).
// Reference oracle: a from-scratch "lowest asserted index wins" model, independent of the
// RTL's binary-tree implementation.
#include "Vprim_arbiter_fixed.h"
#include "verilated.h"
#include <cstdint>
#include <cstdio>
#include <random>

static vluint64_t g_time = 0;
double sc_time_stamp() { return static_cast<double>(g_time); }

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  Vprim_arbiter_fixed* dut = new Vprim_arbiter_fixed;

  std::mt19937 rng(20261002);
  std::uniform_int_distribution<int> req_dist(0, 255);
  std::uniform_int_distribution<int> bit_dist(0, 1);
  std::uniform_int_distribution<uint32_t> data_dist(0, 0xFFFFFFFFu);

  dut->clk_i = 0;
  dut->rst_ni = 1;

  int n_trials = 2000;
  int mismatches = 0;
  for (int t = 0; t < n_trials; t++) {
    uint8_t req = static_cast<uint8_t>(req_dist(rng));
    uint8_t ready = static_cast<uint8_t>(bit_dist(rng));
    uint32_t data[8];
    for (int i = 0; i < 8; i++) data[i] = data_dist(rng);

    dut->req_i = req;
    dut->ready_i = ready;
    for (int i = 0; i < 8; i++) dut->data_i[i] = data[i];
    dut->eval();

    // Reference: lowest set bit of req wins.
    int exp_idx = -1;
    for (int i = 0; i < 8; i++) {
      if (req & (1 << i)) { exp_idx = i; break; }
    }
    bool exp_valid = (exp_idx != -1);
    uint8_t exp_gnt = (exp_valid && ready) ? (1u << exp_idx) : 0;
    uint32_t exp_data = exp_valid ? data[exp_idx] : 0;

    bool ok = true;
    if (static_cast<bool>(dut->valid_o) != exp_valid) ok = false;
    if (dut->gnt_o != exp_gnt) ok = false;
    if (exp_valid && dut->idx_o != static_cast<uint8_t>(exp_idx)) ok = false;
    if (exp_valid && ready && dut->data_o != exp_data) ok = false;

    if (!ok) {
      mismatches++;
      if (mismatches <= 5) {
        std::fprintf(stderr,
                     "mismatch at trial %d: req=0x%02x ready=%d -> rtl(valid=%d gnt=0x%02x "
                     "idx=%d data=0x%08x) exp(valid=%d idx=%d)\n",
                     t, req, ready, dut->valid_o, dut->gnt_o, dut->idx_o, dut->data_o, exp_valid,
                     exp_idx);
      }
    }
  }

  std::printf("prim_arbiter_fixed: %d/%d trials matched the fixed-priority reference\n",
              n_trials - mismatches, n_trials);
  dut->final();
  delete dut;
  return mismatches == 0 ? 0 : 1;
}
