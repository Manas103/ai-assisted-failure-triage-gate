"""Runs clustering and attribution over the full DuckDB record set and
writes the raw measurement reports under docs/. This is the script the
README's Validation section names.
"""

import json
import sys
from pathlib import Path

import duckdb

from triage.attribute import attribute_batch, score_accuracy
from triage.cluster import cluster_records, score_recovery
from triage.signatures import ALL_SIGNATURES, SIGNATURES_BY_ID


def load_records(db_path):
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute(
        "SELECT record_id, error_type, message, stack_trace FROM failure_records ORDER BY record_id"
    ).fetchall()
    gt_rows = con.execute("SELECT record_id, signature_id FROM ground_truth").fetchall()
    con.close()
    records = [
        {"record_id": r[0], "error_type": r[1], "message": r[2], "stack_trace": r[3]}
        for r in rows
    ]
    ground_truth = {r[0]: r[1] for r in gt_rows}
    return records, ground_truth


def main(db_path, docs_dir):
    docs_dir = Path(docs_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)
    records, ground_truth = load_records(db_path)
    n = len(records)

    clusters = cluster_records(records)
    recovered, sig_report = score_recovery(clusters, ground_truth)

    attributions = attribute_batch(records)
    correct, total, accuracy = score_accuracy(attributions, ground_truth)

    lines = []
    lines.append(f"Records loaded: {n}")
    lines.append(f"Distinct clusters formed: {len(clusters)}")
    lines.append(f"True signatures recovered: {recovered} / {len(ALL_SIGNATURES)}")
    lines.append("")
    lines.append("Per-signature recovery:")
    for sid in sorted(sig_report):
        rep = sig_report[sid]
        sig = SIGNATURES_BY_ID[sid]
        lines.append(
            f"  sig {sid:02d} ({sig['key']}): recovered={rep['recovered']} "
            f"coverage={rep.get('coverage')} purity={rep.get('purity')} "
            f"true_count={rep.get('true_count')} cluster_size={rep.get('cluster_size')}"
        )
    (docs_dir / "clustering_results.txt").write_text("\n".join(lines), encoding="utf-8")

    exact = sum(1 for v in attributions.values() if v[1] == "exact")
    nearest = n - exact
    lines2 = []
    lines2.append(f"Records attributed: {n}")
    lines2.append(f"Correct: {correct} / {total} = {accuracy * 100:.2f}%")
    lines2.append(f"Matched by exact normalized-template lookup: {exact}")
    lines2.append(f"Matched by nearest-neighbor fallback: {nearest}")
    lines2.append("")
    lines2.append("Per-signature accuracy:")
    per_sig_total = {}
    per_sig_correct = {}
    for rid, sid in ground_truth.items():
        per_sig_total[sid] = per_sig_total.get(sid, 0) + 1
        if attributions[rid][0] == sid:
            per_sig_correct[sid] = per_sig_correct.get(sid, 0) + 1
    for sid in sorted(per_sig_total):
        t = per_sig_total[sid]
        c = per_sig_correct.get(sid, 0)
        sig = SIGNATURES_BY_ID[sid]
        lines2.append(f"  sig {sid:02d} ({sig['key']}): {c}/{t} = {c/t*100:.1f}%")
    (docs_dir / "attribution_report.txt").write_text("\n".join(lines2), encoding="utf-8")

    summary = {
        "n_records": n,
        "n_clusters": len(clusters),
        "signatures_total": len(ALL_SIGNATURES),
        "signatures_recovered": recovered,
        "attribution_correct": correct,
        "attribution_total": total,
        "attribution_accuracy_pct": round(accuracy * 100, 2),
    }
    (docs_dir / "measure_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/failures.duckdb"
    docs_dir = sys.argv[2] if len(sys.argv) > 2 else "docs"
    main(db_path, docs_dir)
