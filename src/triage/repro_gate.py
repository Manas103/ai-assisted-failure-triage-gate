"""Gate 1: a proposed root cause is accepted only when its generated
reproduction script actually fails against the suspect (buggy) build and
actually passes against the fix build.

The reproduction script is generated fresh per check (a real .py file
written to a temp directory and run with subprocess.run, not a hardcoded
boolean), reusing the REPRO_CASES the fixture's fixed.py already declares.
Both "the suspect fails" and "the fix passes" are measured by two
independent subprocess runs of the identical generated script against
two different target files, so nothing about the eventual accept/reject
decision is precomputed.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"

_SCRIPT_TEMPLATE = '''\
import importlib.util
import sys


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fixed_ref = load_module(r"{fixed_path}", "fixed_ref")
target = load_module(r"{target_path}", "target")
func = getattr(target, "{target_function}")

failures = []
for args, expected in fixed_ref.REPRO_CASES:
    try:
        result = func(*args)
    except Exception as e:
        result = "RAISES:" + type(e).__name__
    if isinstance(expected, str) and expected.startswith("RAISES:"):
        ok = result == expected
    else:
        ok = result == expected
    if not ok:
        failures.append((args, expected, result))

if failures:
    print("REPRO_FAIL")
    for f in failures:
        print(f)
    sys.exit(1)
else:
    print("REPRO_PASS")
    sys.exit(0)
'''


def _write_repro_script(fixed_path, target_path, target_function, workdir):
    script = _SCRIPT_TEMPLATE.format(
        fixed_path=str(fixed_path).replace("\\", "\\\\"),
        target_path=str(target_path).replace("\\", "\\\\"),
        target_function=target_function,
    )
    script_path = Path(workdir) / "generated_repro.py"
    script_path.write_text(script, encoding="utf-8")
    return script_path


def run_repro(script_path):
    proc = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True, text=True, timeout=30,
    )
    return proc.returncode == 0, proc.stdout + proc.stderr


def check_root_cause(sig, target_function=None, suspect_path=None, fix_path=None):
    """Runs the generated repro against suspect_path (default buggy.py)
    and fix_path (default fixed.py) for the given signature dict.

    Returns a dict with the full decision and raw subprocess output for
    both runs, so the gate's reasoning is inspectable, not just a bool.
    """
    fixture_dir = FIXTURES_DIR / sig["module"]
    suspect_path = suspect_path or (fixture_dir / "buggy.py")
    fix_path = fix_path or (fixture_dir / "fixed.py")
    target_function = target_function or sig["target_function"]

    with tempfile.TemporaryDirectory() as workdir:
        suspect_script = _write_repro_script(fix_path, suspect_path, target_function, workdir)
        suspect_ok, suspect_out = run_repro(suspect_script)

    with tempfile.TemporaryDirectory() as workdir:
        fix_script = _write_repro_script(fix_path, fix_path, target_function, workdir)
        fix_ok, fix_out = run_repro(fix_script)

    # suspect_ok True means the repro PASSED on the suspect build, i.e. it
    # did NOT reproduce the bug. We need the repro to FAIL on the suspect.
    repro_fails_on_suspect = not suspect_ok
    repro_passes_on_fix = fix_ok
    accepted = repro_fails_on_suspect and repro_passes_on_fix

    return {
        "signature_id": sig["id"],
        "signature_key": sig["key"],
        "accepted": accepted,
        "repro_fails_on_suspect": repro_fails_on_suspect,
        "repro_passes_on_fix": repro_passes_on_fix,
        "suspect_output": suspect_out.strip(),
        "fix_output": fix_out.strip(),
        "suspect_path": str(suspect_path),
        "fix_path": str(fix_path),
    }
