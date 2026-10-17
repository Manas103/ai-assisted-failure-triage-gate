import random
import sys

sys.path.insert(0, "src")
from triage.protocol.generate_protocol_logs import LAYERS, _corrupt, generate  # noqa: E402


def test_generates_requested_count_and_balanced_layers():
    recs = generate(n_logs=2000)
    assert len(recs) == 2000
    counts = {l: 0 for l in LAYERS}
    for r in recs:
        counts[r["layer"]] += 1
    for l in LAYERS:
        assert counts[l] == 400  # 2000 / 5 layers, exactly balanced by construction


def test_same_seed_is_reproducible():
    a = generate(n_logs=500, seed=42)
    b = generate(n_logs=500, seed=42)
    assert [r["message"] for r in a] == [r["message"] for r in b]


def test_corruption_changes_most_messages_at_rate_0_4():
    rng = random.Random(0)
    original = "RSRP measurement -103 dBm on carrier 3, below cell-select threshold"
    n_diff = sum(1 for _ in range(200) if _corrupt(original, rng, rate=0.4) != original)
    assert n_diff > 190  # at 40% per-character corruption, an unchanged message is rare


def test_zero_corrupt_rate_leaves_messages_clean():
    recs = generate(n_logs=50, corrupt_rate=0.0)
    assert all("{" not in r["message"] for r in recs)  # no leftover placeholders
