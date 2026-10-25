# Provenance

The 8 SystemVerilog files in this directory (`prim_crc32.sv`, `prim_arbiter_fixed.sv`,
`prim_slicer.sv`, `prim_max_tree.sv`, `prim_onehot_check.sv`, `prim_sum_tree.sv`,
`prim_leading_one_ppc.sv`, `prim_onehot_enc.sv`), plus their shared support files
(`prim_util_pkg.sv`, `prim_assert.sv` and its four `.svh` macro headers, `prim_flop_macros.sv`,
not themselves counted among the 8 blocks) are copied unmodified from the public
[lowRISC/opentitan](https://github.com/lowRISC/opentitan) repository, directory
`hw/ip/prim/rtl/`, commit `478afb033bb2d3e62cb4c5dd097f578de461b2b5` (2026-10-24), under the
Apache License, Version 2.0 (see `LICENSE` in this directory). No modification was made to any
file in this directory.

These 8 were chosen, out of the ~140 files in that directory, because each compiles and lints
standalone under Verilator 4.038 with at most `prim_assert.sv`'s macro headers (verified with
`verilator --lint-only -sv`); most `prim_*` modules in that directory pull in a package
(`prim_pkg`, `prim_cipher_pkg`, `prim_subreg_pkg`, ...) or instantiate a sibling primitive
(`prim_flop_2sync`, `prim_buf`, ...) that would have had to be pulled in as well, which this
repo's build intentionally avoids to keep the dependency surface small and inspectable.

`../buggy/` holds one deliberately defective copy of each of the 8 files (one single-expression
defect per file, see each file's `BUG:` comment and `src/triage/dv/blocks.py`), used only by the
simulator reproduction gate (`src/triage/dv/sim_repro_gate.py`) to prove that gate can tell a real
suspect build from a real fix by actually compiling and simulating both with Verilator, not by
string comparison. The defects are original to this repo, not taken from OpenTitan's own history.

One substitution from the original 8 candidates: `prim_cdc_rand_delay.sv` lints and instantiates
standalone, but its `DataWidth > 32` branch calls `std::randomize()`, which the open-source
Verilator 4.038 used to build this repo does not implement, so it cannot be compiled at all here
regardless of simulation parameters (the branch is a runtime `if`, not a generate construct, so
Verilator must still elaborate it). It was swapped for `prim_onehot_enc.sv`, a 21-line one-hot
encoder, equally standalone and equally real.
