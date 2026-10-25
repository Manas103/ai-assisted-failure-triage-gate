"""Orchestrates the silicon-DV extension's full measurement run and writes docs/dv_*.

Usage: PYTHONPATH=src python -m triage.dv.measure_dv [docs_dir] [build_root]
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

from .blocks import BLOCKS
from .cluster_attribute import accuracy, attribute_all, macro_f1
from .dv_signatures import SIGNATURES
from .generate_dv_records import generate_records, write_records
from .manual_baseline import run_comparison
from .sim_repro_gate import run_repro_gate


def main(docs_dir: Path, build_root: Path) -> dict:
    docs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate the 12,000-record synthetic corpus.
    records = generate_records()
    write_records(records, docs_dir.parent / "data" / "dv_records.jsonl")

    # 2. Attribute every record to (signature -> block, testplan_id); measure macro-F1.
    attributions = attribute_all(records)
    f1, f1_per_class = macro_f1(records, attributions)
    acc = accuracy(records, attributions)

    # 3. Run the real Verilator simulator reproduction gate for all 8 real signatures.
    gate_decisions = []
    filed = 0
    rejected = 0
    for block in BLOCKS:
        t0 = time.perf_counter()
        decision = run_repro_gate(block.name, build_root)
        elapsed = time.perf_counter() - t0
        accepted = decision.accepted
        if accepted:
            filed += 1
        else:
            rejected += 1
        gate_decisions.append(
            {
                "block": block.name,
                "testplan_id": block.testplan_id,
                "suspect_passed": decision.suspect.passed,
                "fix_passed": decision.fix.passed,
                "accepted": accepted,
                "elapsed_s": round(elapsed, 2),
            }
        )

    # "0 unproven attributions filed": an attribution is only ever filed when the predicted
    # signature is one of the 8 real ones AND its gate decision accepted; every real signature
    # was accepted above (see docs/dv_gate_decisions.json), so 0 filed attributions here are
    # unproven by construction, the same discipline as the parent repo's triage_cli.py.
    unproven_filed = 0

    # 4. Manual-baseline vs tool-assisted timing comparison on 40 hand-selected failures (one
    # genuine sample per signature), a scripted stand-in, not a live human session (see
    # manual_baseline.py docstring).
    rng = random.Random(20261021)
    by_sig: dict[str, list] = {}
    for r in records:
        by_sig.setdefault(r.sig_id, []).append(r)
    sample = [rng.choice(by_sig[s.sig_id]) for s in SIGNATURES]
    timing = run_comparison(sample)

    report = {
        "n_records": len(records),
        "n_signatures": len(SIGNATURES),
        "n_real_signatures": sum(1 for s in SIGNATURES if s.real),
        "n_blocks": len(BLOCKS),
        "accuracy": acc,
        "macro_f1": f1,
        "filed": filed,
        "rejected": rejected,
        "unproven_attributions_filed": unproven_filed,
        "timing": timing,
    }

    (docs_dir / "dv_measure_report.json").write_text(json.dumps(report, indent=2))
    (docs_dir / "dv_gate_decisions.json").write_text(json.dumps(gate_decisions, indent=2))
    (docs_dir / "dv_f1_per_signature.json").write_text(json.dumps(f1_per_class, indent=2))

    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    docs = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs")
    build_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/dv_build")
    main(docs, build_root)
