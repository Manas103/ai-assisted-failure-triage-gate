from triage.cluster import cluster_records, normalize, score_recovery
from triage.generate_records import generate


def test_generate_is_deterministic_for_a_fixed_seed():
    a = generate(seed=111, n_records=200)
    b = generate(seed=111, n_records=200)
    assert [r["signature_id"] for r in a] == [r["signature_id"] for r in b]
    assert [r["message"] for r in a] == [r["message"] for r in b]


def test_generate_covers_all_40_signatures_at_reasonable_scale():
    records = generate(seed=222, n_records=2000)
    seen = {r["signature_id"] for r in records}
    assert seen == set(range(1, 41))


def test_normalize_strips_volatile_tokens():
    a = normalize("AssertionError", "failed for user_1049503, code 805", "line 42 addr 0xabc123def456")
    b = normalize("AssertionError", "failed for user_29, code 6", "line 900001 addr 0x1112223334")
    assert a == b


def test_normalize_strips_numbers_immediately_followed_by_a_unit_letter():
    # regression test for the real bug found and fixed this session: a bare
    # \b\d+\b regex does not match a digit run directly followed by a word
    # character (e.g. "710s"), because there is no word boundary there.
    a = normalize("Err", "waited 710s for it", "")
    b = normalize("Err", "waited 12s for it", "")
    assert a == b


def test_cluster_recovers_known_signatures_on_a_small_batch():
    records = generate(seed=333, n_records=2000)
    ground_truth = {r["record_id"]: r["signature_id"] for r in records}
    clusters = cluster_records(records)
    recovered, report = score_recovery(clusters, ground_truth)
    assert recovered >= 35  # allow some slack at smaller batch sizes
    assert recovered <= 40
