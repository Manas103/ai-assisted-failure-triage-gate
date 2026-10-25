# DV testplan: silicon-DV regression triage extension

One entry per signature (dv_signatures.py), in the same top-to-bottom order
`manual_baseline.py`'s scripted stand-in scans them in. The 8 entries marked **real** are the
only ones a reported root-cause attribution can ever be *filed* against, because they are the
only ones with a real buggy/fixed RTL pair behind them (`sim_repro_gate.py`); the other 32 are
textual-pattern-only DV failure categories used to exercise clustering and attribution at the
full 12,000-record scale (see README "Honest framing").

| Testplan ID | Block | Real | Description |
|---|---|---|---|
| PRIM_CRC32_FUNCTIONAL_0001 | prim_crc32 | real | CRC32 output value correctness against the standard IEEE/zlib CRC32 reference |
| PRIM_CRC32_ASSERTION_TIMING_0101 | prim_crc32 | textual | Unknown (X/Z) value observed on a crc32 output |
| PRIM_CRC32_PROTOCOL_VIOLATION_0102 | prim_crc32 | textual | ready/valid protocol violation around the crc32 interface |
| PRIM_CRC32_RANDOMIZATION_FAILURE_0103 | prim_crc32 | textual | Constraint solver failure building a crc32 stimulus item |
| PRIM_CRC32_SCOREBOARD_TIMEOUT_0104 | prim_crc32 | textual | Scoreboard timeout waiting for a crc32 response |
| PRIM_ARBITER_FIXED_PRIORITY_0002 | prim_arbiter_fixed | real | Fixed-priority grant order (lowest index wins) against a from-scratch reference |
| PRIM_ARBITER_FIXED_ASSERTION_TIMING_0101 | prim_arbiter_fixed | textual | Unknown (X/Z) value observed on an arbiter output |
| PRIM_ARBITER_FIXED_PROTOCOL_VIOLATION_0102 | prim_arbiter_fixed | textual | ready/valid protocol violation around the arbiter interface |
| PRIM_ARBITER_FIXED_RANDOMIZATION_FAILURE_0103 | prim_arbiter_fixed | textual | Constraint solver failure building an arbiter stimulus item |
| PRIM_ARBITER_FIXED_SCOREBOARD_TIMEOUT_0104 | prim_arbiter_fixed | textual | Scoreboard timeout waiting for an arbiter response |
| PRIM_SLICER_CHUNK_INDEX_0003 | prim_slicer | real | Selected output chunk matches the requested index against a from-scratch reference |
| PRIM_SLICER_ASSERTION_TIMING_0101 | prim_slicer | textual | Unknown (X/Z) value observed on a slicer output |
| PRIM_SLICER_PROTOCOL_VIOLATION_0102 | prim_slicer | textual | ready/valid protocol violation around the slicer interface |
| PRIM_SLICER_RANDOMIZATION_FAILURE_0103 | prim_slicer | textual | Constraint solver failure building a slicer stimulus item |
| PRIM_SLICER_SCOREBOARD_TIMEOUT_0104 | prim_slicer | textual | Scoreboard timeout waiting for a slicer response |
| PRIM_MAX_TREE_BOTH_VALID_0004 | prim_max_tree | real | Both-valid maximum selection against a from-scratch reference |
| PRIM_MAX_TREE_ASSERTION_TIMING_0101 | prim_max_tree | textual | Unknown (X/Z) value observed on a max_tree output |
| PRIM_MAX_TREE_PROTOCOL_VIOLATION_0102 | prim_max_tree | textual | ready/valid protocol violation around the max_tree interface |
| PRIM_MAX_TREE_RANDOMIZATION_FAILURE_0103 | prim_max_tree | textual | Constraint solver failure building a max_tree stimulus item |
| PRIM_MAX_TREE_SCOREBOARD_TIMEOUT_0104 | prim_max_tree | textual | Scoreboard timeout waiting for a max_tree response |
| PRIM_ONEHOT_CHECK_CONFLICT_GATE_0005 | prim_onehot_check | real | One-hot0 conflict detection against a popcount reference |
| PRIM_ONEHOT_CHECK_ASSERTION_TIMING_0101 | prim_onehot_check | textual | Unknown (X/Z) value observed on a onehot_check output |
| PRIM_ONEHOT_CHECK_PROTOCOL_VIOLATION_0102 | prim_onehot_check | textual | ready/valid protocol violation around the onehot_check interface |
| PRIM_ONEHOT_CHECK_RANDOMIZATION_FAILURE_0103 | prim_onehot_check | textual | Constraint solver failure building a onehot_check stimulus item |
| PRIM_ONEHOT_CHECK_SCOREBOARD_TIMEOUT_0104 | prim_onehot_check | textual | Scoreboard timeout waiting for a onehot_check response |
| PRIM_SUM_TREE_SINGLE_VALID_0006 | prim_sum_tree | real | Single-valid forwarding and sum-of-valid total against a from-scratch reference |
| PRIM_SUM_TREE_ASSERTION_TIMING_0101 | prim_sum_tree | textual | Unknown (X/Z) value observed on a sum_tree output |
| PRIM_SUM_TREE_PROTOCOL_VIOLATION_0102 | prim_sum_tree | textual | ready/valid protocol violation around the sum_tree interface |
| PRIM_SUM_TREE_RANDOMIZATION_FAILURE_0103 | prim_sum_tree | textual | Constraint solver failure building a sum_tree stimulus item |
| PRIM_SUM_TREE_SCOREBOARD_TIMEOUT_0104 | prim_sum_tree | textual | Scoreboard timeout waiting for a sum_tree response |
| PRIM_LEADING_ONE_PPC_PREFIX_0007 | prim_leading_one_ppc | real | Lowest-set-bit index against a from-scratch reference |
| PRIM_LEADING_ONE_PPC_ASSERTION_TIMING_0101 | prim_leading_one_ppc | textual | Unknown (X/Z) value observed on a leading_one_ppc output |
| PRIM_LEADING_ONE_PPC_PROTOCOL_VIOLATION_0102 | prim_leading_one_ppc | textual | ready/valid protocol violation around the leading_one_ppc interface |
| PRIM_LEADING_ONE_PPC_RANDOMIZATION_FAILURE_0103 | prim_leading_one_ppc | textual | Constraint solver failure building a leading_one_ppc stimulus item |
| PRIM_LEADING_ONE_PPC_SCOREBOARD_TIMEOUT_0104 | prim_leading_one_ppc | textual | Scoreboard timeout waiting for a leading_one_ppc response |
| PRIM_ONEHOT_ENC_BIT_SELECT_0008 | prim_onehot_enc | real | Selected one-hot output bit against a from-scratch reference |
| PRIM_ONEHOT_ENC_ASSERTION_TIMING_0101 | prim_onehot_enc | textual | Unknown (X/Z) value observed on a onehot_enc output |
| PRIM_ONEHOT_ENC_PROTOCOL_VIOLATION_0102 | prim_onehot_enc | textual | ready/valid protocol violation around the onehot_enc interface |
| PRIM_ONEHOT_ENC_RANDOMIZATION_FAILURE_0103 | prim_onehot_enc | textual | Constraint solver failure building a onehot_enc stimulus item |
| PRIM_ONEHOT_ENC_SCOREBOARD_TIMEOUT_0104 | prim_onehot_enc | textual | Scoreboard timeout waiting for a onehot_enc response |
