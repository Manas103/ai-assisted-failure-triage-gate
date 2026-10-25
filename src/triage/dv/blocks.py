"""Registry of the 8 public OpenTitan `prim_*` blocks this extension triages against.

Each entry names the real RTL file (see ../../../third_party/opentitan_prim/PROVENANCE.md),
the Verilator top module and parameter overrides needed to build a small, concrete instance of
it, any extra source files it needs (a shared package, for prim_leading_one_ppc), and the
one-line defect planted in the matching file under ../../../third_party/buggy/ (see each file's
`BUG:` comment). This is the single source of truth `sim_repro_gate.py`, `dv_signatures.py` and
the testplan both read from.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Block:
    name: str
    rtl_file: str
    top_module: str
    testbench: str
    testplan_id: str
    defect_summary: str
    extra_sources: tuple[str, ...] = field(default_factory=tuple)
    params: tuple[str, ...] = field(default_factory=tuple)  # verilator -G... overrides
    defines: tuple[str, ...] = field(default_factory=tuple)  # verilator -D... defines


BLOCKS: list[Block] = [
    Block(
        name="prim_crc32",
        rtl_file="prim_crc32.sv",
        top_module="prim_crc32",
        testbench="tb_prim_crc32.cpp",
        testplan_id="PRIM_CRC32_FUNCTIONAL_0001",
        defect_summary="dropped output inversion: crc_out_o = crc_q instead of ~crc_q",
    ),
    Block(
        name="prim_arbiter_fixed",
        rtl_file="prim_arbiter_fixed.sv",
        top_module="prim_arbiter_fixed",
        testbench="tb_prim_arbiter_fixed.cpp",
        testplan_id="PRIM_ARBITER_FIXED_PRIORITY_0002",
        defect_summary="inverted tree select polarity: priority flipped from lowest to highest index",
    ),
    Block(
        name="prim_slicer",
        rtl_file="prim_slicer.sv",
        top_module="prim_slicer",
        testbench="tb_prim_slicer.cpp",
        testplan_id="PRIM_SLICER_CHUNK_INDEX_0003",
        defect_summary="off-by-one chunk index: selects slice (sel_i+1) instead of sel_i",
    ),
    Block(
        name="prim_max_tree",
        rtl_file="prim_max_tree.sv",
        top_module="prim_max_tree",
        testbench="tb_prim_max_tree.cpp",
        testplan_id="PRIM_MAX_TREE_BOTH_VALID_0004",
        defect_summary="flipped '>' to '<' in the both-valid comparator: forwards the minimum, not the maximum",
        params=("NumSrc=4", "Width=8"),
    ),
    Block(
        name="prim_onehot_check",
        rtl_file="prim_onehot_check.sv",
        top_module="prim_onehot_check",
        testbench="tb_prim_onehot_check.cpp",
        testplan_id="PRIM_ONEHOT_CHECK_CONFLICT_GATE_0005",
        defect_summary="changed conflict AND to OR: flags almost every legitimate one-hot input as an error",
        params=("AddrCheck=0", "EnableCheck=0"),
    ),
    Block(
        name="prim_sum_tree",
        rtl_file="prim_sum_tree.sv",
        top_module="prim_sum_tree",
        testbench="tb_prim_sum_tree.cpp",
        testplan_id="PRIM_SUM_TREE_SINGLE_VALID_0006",
        defect_summary="swapped the two single-valid forwarding arms in the node-sum mux",
        params=("NumSrc=4", "InWidth=8", "Saturate=0"),
    ),
    Block(
        name="prim_leading_one_ppc",
        rtl_file="prim_leading_one_ppc.sv",
        top_module="prim_leading_one_ppc",
        testbench="tb_prim_leading_one_ppc.cpp",
        testplan_id="PRIM_LEADING_ONE_PPC_PREFIX_0007",
        defect_summary="prefix-OR changed to prefix-AND: collapses at the first zero bit below the target",
        extra_sources=("prim_util_pkg.sv",),
    ),
    Block(
        name="prim_onehot_enc",
        rtl_file="prim_onehot_enc.sv",
        top_module="prim_onehot_enc",
        testbench="tb_prim_onehot_enc.cpp",
        testplan_id="PRIM_ONEHOT_ENC_BIT_SELECT_0008",
        defect_summary="changed the per-bit AND to OR: every bit goes high whenever en_i is set",
    ),
]

BLOCKS_BY_NAME = {b.name: b for b in BLOCKS}

assert len(BLOCKS) == 8
