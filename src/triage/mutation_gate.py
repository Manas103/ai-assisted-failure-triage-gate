"""Gate 2: a proposed regression test is admitted only when it kills the
mutant standing in for its defect.

`mutmut` (checked into requirements-dev via a clean `pip install mutmut`
in this project's venv, see README) mutates broadly across a whole module
and reports an aggregate score; it has no notion of "the one mutant that
represents this specific seeded defect" tied to "this one proposed test".
That per-defect correspondence is exactly what this gate needs, so the
mutants here are hand-rolled: each real fixture's fixed.py declares a
small MUTANTS list (description, find-text, replace-text) representing
plausible variants of its own defect class (flipped comparator, shifted
boundary, swapped branch), applied as a real text patch to a real
temporary copy of fixed.py and executed, never simulated.

A proposed test is a set of (args, expected) cases, structurally the
same shape as a fixture's REPRO_CASES (see repro_gate.py's generated
script, reused here unchanged). The test is admitted only if it:
  1. passes when run against the untouched fixed.py, and
  2. fails ("kills the mutant") against every one of that fixture's
     hand-rolled mutants.
Either condition failing means refuse.
"""

import importlib.util
import tempfile
from pathlib import Path

from triage.repro_gate import FIXTURES_DIR, _write_repro_script, run_repro


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_fixed_module(sig):
    fixed_path = FIXTURES_DIR / sig["module"] / "fixed.py"
    return _load_module(fixed_path, f"{sig['key']}_fixed_ref")


def apply_mutant(fixed_source_path, find, replace, workdir):
    src = Path(fixed_source_path).read_text(encoding="utf-8")
    if find not in src:
        raise ValueError(f"mutant find-pattern not present in {fixed_source_path}: {find!r}")
    mutant_src = src.replace(find, replace, 1)
    mutant_path = Path(workdir) / "mutant.py"
    mutant_path.write_text(mutant_src, encoding="utf-8")
    return mutant_path


def _run_cases(cases_source_path, target_path, target_function):
    with tempfile.TemporaryDirectory() as wd:
        script = _write_repro_script(cases_source_path, target_path, target_function, wd)
        return run_repro(script)


def check_mutant_killed(sig, description, find, replace, test_cases_path=None, target_function=None):
    fixture_dir = FIXTURES_DIR / sig["module"]
    fixed_path = fixture_dir / "fixed.py"
    test_cases_path = test_cases_path or fixed_path
    target_function = target_function or sig["target_function"]

    passes_on_fixed, out_fixed = _run_cases(test_cases_path, fixed_path, target_function)

    with tempfile.TemporaryDirectory() as wd:
        mutant_path = apply_mutant(fixed_path, find, replace, wd)
        passes_on_mutant, out_mutant = _run_cases(test_cases_path, mutant_path, target_function)

    killed = passes_on_fixed and (not passes_on_mutant)
    return {
        "signature_id": sig["id"],
        "signature_key": sig["key"],
        "mutant_description": description,
        "passes_on_fixed": passes_on_fixed,
        "passes_on_mutant": passes_on_mutant,
        "killed": killed,
        "fixed_output": out_fixed.strip(),
        "mutant_output": out_mutant.strip(),
    }


def check_test_admission(sig, test_cases_path=None, target_function=None):
    """Runs every hand-rolled mutant for this signature's fixture and
    decides whether the proposed test (test_cases_path, default the
    fixture's own REPRO_CASES in fixed.py) is admitted."""
    fixed_module = load_fixed_module(sig)
    mutants = getattr(fixed_module, "MUTANTS", [])
    results = [
        check_mutant_killed(sig, desc, find, replace, test_cases_path, target_function)
        for desc, find, replace in mutants
    ]
    all_killed = bool(results) and all(r["killed"] for r in results)
    any_broken_on_fixed = any(not r["passes_on_fixed"] for r in results)
    admitted = all_killed and not any_broken_on_fixed
    return {
        "signature_id": sig["id"],
        "signature_key": sig["key"],
        "mutant_count": len(results),
        "killed_count": sum(1 for r in results if r["killed"]),
        "admitted": admitted,
        "mutant_results": results,
    }
