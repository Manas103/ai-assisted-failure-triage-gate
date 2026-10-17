import sys

sys.path.insert(0, "src")
from triage.protocol.deterministic_router import route  # noqa: E402
from triage.protocol.generate_protocol_logs import generate  # noqa: E402


def test_clean_message_is_always_attributed():
    recs = generate(n_logs=200, corrupt_rate=0.0)
    for r in recs:
        m = route(r["message"])
        assert m["attributed"]
        assert m["step"] is not None
        assert m["layer"] == r["layer"]  # an uncorrupted message should match its own layer


def test_residue_fraction_near_claimed_11_percent():
    recs = generate(n_logs=4000)  # default corrupt_rate=0.4, same as the full 22,000-log corpus
    n_residue = sum(1 for r in recs if not route(r["message"])["attributed"])
    frac = n_residue / len(recs)
    assert 0.05 < frac < 0.20  # a generous band around 0.11; the exact number is in docs/


def test_residue_record_has_no_step():
    recs = generate(n_logs=500)
    residue = [r for r in recs if not route(r["message"])["attributed"]]
    assert len(residue) > 0
    for r in residue[:20]:
        m = route(r["message"])
        assert m["step"] is None
