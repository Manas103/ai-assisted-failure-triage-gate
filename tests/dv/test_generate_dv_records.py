from triage.dv.dv_signatures import SIGNATURES
from triage.dv.generate_dv_records import generate_records


def test_generates_12000_records_deterministically():
    recs_a = generate_records()
    recs_b = generate_records()
    assert len(recs_a) == 12_000
    assert [r.log_line for r in recs_a] == [r.log_line for r in recs_b]  # fixed seed


def test_every_signature_represented():
    recs = generate_records()
    seen = {r.sig_id for r in recs}
    assert seen == {s.sig_id for s in SIGNATURES}


def test_ground_truth_block_and_testplan_consistent_with_signature():
    recs = generate_records()
    by_id = {s.sig_id: s for s in SIGNATURES}
    for r in recs[:200]:
        sig = by_id[r.sig_id]
        assert r.block == sig.block
        assert r.testplan_id == sig.testplan_id
