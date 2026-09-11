import pytest

from triage.mutation_gate import check_test_admission
from triage.repro_gate import check_root_cause
from triage.signatures import REAL_SIGNATURES, SIGNATURES_BY_ID


@pytest.mark.parametrize("sig", REAL_SIGNATURES, ids=[s["key"] for s in REAL_SIGNATURES])
def test_repro_gate_accepts_the_real_root_cause_for_every_real_fixture(sig):
    result = check_root_cause(sig)
    assert result["repro_fails_on_suspect"] is True, result["suspect_output"]
    assert result["repro_passes_on_fix"] is True, result["fix_output"]
    assert result["accepted"] is True


def test_repro_gate_rejects_a_wrong_candidate_fix():
    # Negative control: propose the buggy build itself as the "fix". The
    # repro must not pass against it, so the gate must refuse.
    sig = SIGNATURES_BY_ID[1]
    fixture_dir = __import__("triage.repro_gate", fromlist=["FIXTURES_DIR"]).FIXTURES_DIR / sig["module"]
    result = check_root_cause(sig, suspect_path=fixture_dir / "buggy.py", fix_path=fixture_dir / "buggy.py")
    assert result["accepted"] is False


@pytest.mark.parametrize("sig", REAL_SIGNATURES, ids=[s["key"] for s in REAL_SIGNATURES])
def test_mutation_gate_runs_for_every_real_fixture(sig):
    result = check_test_admission(sig)
    assert result["mutant_count"] >= 1
    # every mutant result must at least report cleanly (no crash) and
    # correctly show the test passes on the untouched fixed.py
    for mr in result["mutant_results"]:
        assert mr["passes_on_fixed"] is True, mr["fixed_output"]


def test_mutation_gate_admits_most_of_the_real_fixtures():
    admitted = sum(1 for sig in REAL_SIGNATURES if check_test_admission(sig)["admitted"])
    # two of the twelve are known, disclosed equivalent-mutant survivors
    # (see README Findings); the other ten must be admitted.
    assert admitted >= 10
