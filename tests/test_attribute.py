from triage.attribute import attribute_batch, score_accuracy
from triage.generate_records import generate


def test_attribution_matches_ground_truth_on_a_batch():
    records = generate(seed=444, n_records=1000)
    ground_truth = {r["record_id"]: r["signature_id"] for r in records}
    attributions = attribute_batch(records)
    correct, total, accuracy = score_accuracy(attributions, ground_truth)
    assert total == 1000
    assert accuracy >= 0.90


def test_attribution_returns_a_method_label():
    records = generate(seed=555, n_records=50)
    attributions = attribute_batch(records)
    for sig_id, method in attributions.values():
        assert method in ("exact", "nearest")
        assert 1 <= sig_id <= 40
