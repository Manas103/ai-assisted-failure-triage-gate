import sys

sys.path.insert(0, "src")
from triage.protocol.escalate import escalate_batch, escalate_one, has_citation_before_step  # noqa: E402
from triage.protocol.retrieval import TfidfIndex  # noqa: E402


def test_has_citation_before_step_true_for_well_formed_text():
    assert has_citation_before_step("[cites Internal Debug Spec S1.1 (phy_rsrp)] do the thing, next step.")


def test_has_citation_before_step_false_when_step_comes_first():
    assert not has_citation_before_step("Do the thing first. [cites Internal Debug Spec S1.1 (phy_rsrp)]")


def test_has_citation_before_step_false_with_no_citation():
    assert not has_citation_before_step("Just do the thing, no citation at all.")


def test_escalate_one_always_cites_before_step():
    index = TfidfIndex()
    out = escalate_one("RSRP measurement -103 dBm on carrier 3", index)
    assert has_citation_before_step(out["step"])


def test_escalate_batch_every_record_cites_before_step():
    index = TfidfIndex()
    fake_records = [
        {"record_id": 0, "message": "sbfer statsreprt missing or loicalcnneb"},
        {"record_id": 1, "message": "garbled mac rach preamble collisio3n"},
    ]
    out = escalate_batch(fake_records, index)
    assert len(out) == 2
    for v in out.values():
        assert has_citation_before_step(v["step"])
