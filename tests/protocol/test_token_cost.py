import sys

sys.path.insert(0, "src")
from triage.protocol.retrieval import TfidfIndex  # noqa: E402
from triage.protocol.token_cost import measure  # noqa: E402


def test_measure_ratio_matches_residue_fraction_lower_bound():
    """The escalated path sends fewer calls AND fewer tokens per call than
    the naive path, so its cost ratio must be strictly below the pure
    residue-fraction ratio (which only accounts for fewer calls)."""
    all_records = [{"record_id": i, "message": f"test message number {i} with some content"} for i in range(100)]
    residue_records = all_records[:11]  # 11% residue, same shape as the real measurement
    index = TfidfIndex()
    out = measure(all_records, residue_records, router_matches=None, index=index)
    assert out["n_total"] == 100
    assert out["n_residue"] == 11
    assert out["cost_ratio"] < 0.11  # strictly better than "just fewer calls" would give
    assert out["cost_reduction_factor"] > 9.0


def test_measure_handles_zero_residue():
    all_records = [{"record_id": i, "message": "clean message"} for i in range(10)]
    index = TfidfIndex()
    out = measure(all_records, [], router_matches=None, index=index)
    assert out["n_residue"] == 0
    assert out["cost_ratio"] == 0.0
