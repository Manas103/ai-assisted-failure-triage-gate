"""Direct, in-process pytest coverage of every real fixture's fixed.py,
independent of the subprocess-based gates in test_gates.py. This is the
plain "real tests" layer BUILDER.md requires in addition to the gates.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
from triage.signatures import REAL_SIGNATURES  # noqa: E402


def _check_case(func, args, expected):
    try:
        result = func(*args)
    except Exception as e:
        result = f"RAISES:{type(e).__name__}"
    if isinstance(expected, str) and expected.startswith("RAISES:"):
        assert result == expected
    else:
        assert result == expected


@pytest.mark.parametrize("sig", REAL_SIGNATURES, ids=[s["key"] for s in REAL_SIGNATURES])
def test_fixed_module_passes_its_own_repro_cases(sig):
    fixed = _load(FIXTURES_DIR / sig["module"] / "fixed.py", f"{sig['key']}_fixed")
    func = getattr(fixed, sig["target_function"])
    for args, expected in fixed.REPRO_CASES:
        _check_case(func, args, expected)


@pytest.mark.parametrize("sig", REAL_SIGNATURES, ids=[s["key"] for s in REAL_SIGNATURES])
def test_buggy_module_fails_at_least_one_repro_case(sig):
    fixed = _load(FIXTURES_DIR / sig["module"] / "fixed.py", f"{sig['key']}_fixed_ref")
    buggy = _load(FIXTURES_DIR / sig["module"] / "buggy.py", f"{sig['key']}_buggy")
    func = getattr(buggy, sig["target_function"])
    any_failed = False
    for args, expected in fixed.REPRO_CASES:
        try:
            result = func(*args)
        except Exception as e:
            result = f"RAISES:{type(e).__name__}"
        if isinstance(expected, str) and expected.startswith("RAISES:"):
            ok = result == expected
        else:
            ok = result == expected
        if not ok:
            any_failed = True
    assert any_failed, f"buggy.py for {sig['key']} unexpectedly passed every repro case"
