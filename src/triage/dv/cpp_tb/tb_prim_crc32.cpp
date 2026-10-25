// Self-checking Verilator testbench for prim_crc32.
// Reference oracle: a from-scratch bit-serial CRC32 (polynomial 0xEDB88320, init 0xFFFFFFFF,
// final XOR 0xFFFFFFFF -- the standard IEEE/zlib CRC32) sharing no code with the RTL's own
// byte-lookup-table implementation. Feeds BytesPerWord=4-byte words for a mix of random message
// lengths, resets the RTL's internal CRC between messages, and diffs the two exactly.
#include "Vprim_crc32.h"
#include "verilated.h"
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <random>
#include <vector>

static vluint64_t g_time = 0;
double sc_time_stamp() { return static_cast<double>(g_time); }

static uint32_t crc32_reference(const std::vector<uint8_t>& data) {
  uint32_t crc = 0xFFFFFFFFu;
  for (uint8_t b : data) {
    crc ^= b;
    for (int i = 0; i < 8; i++) {
      crc = (crc & 1u) ? ((crc >> 1) ^ 0xEDB88320u) : (crc >> 1);
    }
  }
  return ~crc;
}

static void tick(Vprim_crc32* dut) {
  dut->clk_i = 0;
  dut->eval();
  g_time++;
  dut->clk_i = 1;
  dut->eval();
  g_time++;
}

int main(int argc, char** argv) {
  Verilated::commandArgs(argc, argv);
  Vprim_crc32* dut = new Vprim_crc32;

  std::mt19937 rng(20261001);
  std::uniform_int_distribution<int> byte_dist(0, 255);
  std::uniform_int_distribution<int> len_words_dist(1, 16); // 4..64 bytes

  // Power-on reset.
  dut->rst_ni = 0;
  dut->set_crc_i = 0;
  dut->crc_in_i = 0;
  dut->data_valid_i = 0;
  dut->data_i = 0;
  tick(dut);
  dut->rst_ni = 1;
  tick(dut);

  int n_messages = 200;
  int mismatches = 0;
  for (int m = 0; m < n_messages; m++) {
    int n_words = len_words_dist(rng);
    std::vector<uint8_t> bytes;
    bytes.reserve(n_words * 4);
    for (int i = 0; i < n_words * 4; i++) bytes.push_back(static_cast<uint8_t>(byte_dist(rng)));

    // Reset the RTL's internal CRC register to the "no bytes seen yet" state.
    dut->set_crc_i = 1;
    dut->crc_in_i = 0;
    dut->data_valid_i = 0;
    tick(dut);
    dut->set_crc_i = 0;

    for (int w = 0; w < n_words; w++) {
      uint32_t word = static_cast<uint32_t>(bytes[w * 4]) |
                       (static_cast<uint32_t>(bytes[w * 4 + 1]) << 8) |
                       (static_cast<uint32_t>(bytes[w * 4 + 2]) << 16) |
                       (static_cast<uint32_t>(bytes[w * 4 + 3]) << 24);
      dut->data_i = word;
      dut->data_valid_i = 1;
      tick(dut);
    }
    dut->data_valid_i = 0;

    uint32_t rtl_crc = dut->crc_out_o;
    uint32_t ref_crc = crc32_reference(bytes);
    if (rtl_crc != ref_crc) {
      mismatches++;
      if (mismatches <= 5) {
        std::fprintf(stderr, "mismatch at message %d (%d bytes): rtl=0x%08x ref=0x%08x\n", m,
                     (int)bytes.size(), rtl_crc, ref_crc);
      }
    }
  }

  std::printf("prim_crc32: %d/%d messages matched reference CRC32\n", n_messages - mismatches,
              n_messages);
  dut->final();
  delete dut;
  return mismatches == 0 ? 0 : 1;
}
