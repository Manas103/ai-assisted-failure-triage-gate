"""The one script that ties the whole gate together.

Given the batch of 4,000 failure records already in DuckDB: cluster them,
attribute a signature to every record, then for each of the 12
real-fixture signatures run a proposed root-cause repro through Gate 1
and a proposed regression test through Gate 2. An attribution is filed
only if both gates return green for its signature; otherwise it is
rejected and the reason is printed and written to docs/gate_decisions.txt.

A signature's "count of records this session that would be filed under
it" is every record the deterministic attributor assigned to it, but the
per-signature accept/reject decision itself (the proposal that stands for
all of that signature's records) is checked once, not once per record,
because the root cause and the regression test are properties of the
signature/defect, not of any individual failure record.
"""

import json
import sys
from pathlib import Path

import duckdb

from triage.attribute import attribute_batch
from triage.cluster import cluster_records, score_recovery
from triage.mutation_gate import check_test_admission
from triage.repro_gate import check_root_cause
from triage.signatures import ALL_SIGNATURES, REAL_SIGNATURES, SIGNATURES_BY_ID


def main(db_path, docs_dir):
    docs_dir = Path(docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute(
        "SELECT record_id, error_type, message, stack_trace FROM failure_records ORDER BY record_id"
    ).fetchall()
    gt_rows = con.execute("SELECT record_id, signature_id FROM ground_truth").fetchall()
    con.close()
    records = [{"record_id": r[0], "error_type": r[1], "message": r[2], "stack_trace": r[3]} for r in rows]
    ground_truth = {r[0]: r[1] for r in gt_rows}

    clusters = cluster_records(records)
    recovered, _ = score_recovery(clusters, ground_truth)

    attributions = attribute_batch(records)
    counts_by_sig = {}
    for rid, (sid, _method) in attributions.items():
        counts_by_sig[sid] = counts_by_sig.get(sid, 0) + 1

    decisions = []
    proposals_run = 0
    filed = 0
    rejected = 0
    for sig in REAL_SIGNATURES:
        proposals_run += 1
        repro_result = check_root_cause(sig)
        mutation_result = check_test_admission(sig)
        both_green = repro_result["accepted"] and mutation_result["admitted"]
        record_count = counts_by_sig.get(sig["id"], 0)
        if both_green:
            filed += 1
            reason = "both gates green: repro reproduces the defect and the proposed test kills its mutant(s)"
        else:
            rejected += 1
            reasons = []
            if not repro_result["accepted"]:
                reasons.append("repro gate failed (did not fail-on-suspect/pass-on-fix)")
            if not mutation_result["admitted"]:
                reasons.append(
                    f"mutation gate failed ({mutation_result['killed_count']}/{mutation_result['mutant_count']} mutants killed)"
                )
            reason = "; ".join(reasons)
        decisions.append({
            "signature_id": sig["id"],
            "signature_key": sig["key"],
            "records_attributed_this_batch": record_count,
            "repro_gate_accepted": repro_result["accepted"],
            "mutation_gate_admitted": mutation_result["admitted"],
            "filed": both_green,
            "reason": reason,
        })

    unproven_filed = sum(
        1 for d in decisions if d["filed"] and not (d["repro_gate_accepted"] and d["mutation_gate_admitted"])
    )

    summary = {
        "n_records": len(records),
        "signatures_recovered": recovered,
        "signatures_total": len(ALL_SIGNATURES),
        "real_fixture_proposals_run": proposals_run,
        "filed": filed,
        "rejected": rejected,
        "unproven_attributions_filed": unproven_filed,
        "decisions": decisions,
    }

    lines = [
        f"Batch size: {len(records)} records",
        f"Signatures recovered by clustering: {recovered}/{len(ALL_SIGNATURES)}",
        f"Real-fixture proposals run through both gates this session: {proposals_run}",
        f"Filed: {filed}   Rejected: {rejected}   Unproven attributions filed: {unproven_filed}",
        "",
        f"{'signature':32} {'records':>8} {'repro':>7} {'mutation':>9} {'decision':>10}  reason",
    ]
    for d in decisions:
        lines.append(
            f"{d['signature_key']:32} {d['records_attributed_this_batch']:>8} "
            f"{str(d['repro_gate_accepted']):>7} {str(d['mutation_gate_admitted']):>9} "
            f"{'FILED' if d['filed'] else 'REJECTED':>10}  {d['reason']}"
        )
    (docs_dir / "gate_decisions.txt").write_text("\n".join(lines), encoding="utf-8")
    (docs_dir / "gate_decisions.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n".join(lines))
    return summary


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/failures.duckdb"
    docs_dir = sys.argv[2] if len(sys.argv) > 2 else "docs"
    main(db_path, docs_dir)
