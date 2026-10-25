"""Exercises the real Verilator reproduction gate.

Runs only 2 of the 8 blocks (crc32, onehot_enc: one with a clocked DUT, one purely
combinational) to keep a routine `pytest` run's wall time reasonable; `measure_dv.py` runs the
real gate against all 8 blocks for the measurement captured in docs/dv_gate_decisions.json.
Requires WSL2 Ubuntu-22.04 with verilator installed; skips cleanly if wsl.exe is unavailable.
"""

from pathlib import Path

import pytest

from triage.dv.sim_repro_gate import run_repro_gate


def _wsl_available() -> bool:
    import shutil

    return shutil.which("wsl.exe") is not None


@pytest.mark.skipif(not _wsl_available(), reason="wsl.exe not available on this machine")
@pytest.mark.parametrize("block_name", ["prim_crc32", "prim_onehot_enc"])
def test_suspect_fails_fix_passes(tmp_path, block_name):
    decision = run_repro_gate(block_name, tmp_path)
    assert decision.suspect.passed is False, decision.suspect.stdout
    assert decision.fix.passed is True, decision.fix.stdout
    assert decision.accepted is True
