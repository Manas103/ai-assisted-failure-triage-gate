"""A genuine claude -p cross-check on a small, disclosed live sample.

This is not the attribution mechanism the accuracy claim is measured on
(that is the deterministic classifier in attribute.py, measured over the
full 4,000 records). It is a smaller, real spot-check: a live subprocess
call to `claude -p` asking it to independently name the best-matching
signature for a handful of records, compared against the deterministic
attribution's answer for the same records. Disagreement is expected and
fine; it is reported, not hidden.
"""

import json
import subprocess
import sys
from pathlib import Path

from triage.signatures import ALL_SIGNATURES

SAMPLE_SIZE = 15


def build_prompt(sample_records):
    sig_lines = "\n".join(f"{s['id']}: {s['name']}" for s in ALL_SIGNATURES)
    rec_lines = []
    for r in sample_records:
        rec_lines.append(
            f"record_id={r['record_id']}\nerror_type={r['error_type']}\n"
            f"message={r['message']}\n"
        )
    records_block = "\n".join(rec_lines)
    return (
        "You are triaging CI failure records against a fixed library of 40 "
        "named failure signatures. For each record below, output the single "
        "best-matching signature id (an integer 1-40) based on error_type and "
        "message. Respond with ONLY a JSON object mapping record_id (string) "
        "to signature id (integer), no prose, no markdown fences.\n\n"
        f"Signature library:\n{sig_lines}\n\nRecords:\n{records_block}"
    )


def run_claude_p(prompt, model="claude-haiku-4-5-20251001", timeout=120):
    proc = subprocess.run(
        ["claude", "-p", "--model", model, prompt],
        capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def parse_response(stdout):
    text = stdout.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        raw = json.loads(text[start:end + 1])
        return {int(k): int(v) for k, v in raw.items()}
    except Exception:
        return {}


def main(db_path, docs_dir, sample_size=SAMPLE_SIZE):
    import duckdb
    from triage.attribute import attribute_batch

    docs_dir = Path(docs_dir)
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute(
        "SELECT record_id, error_type, message, stack_trace FROM failure_records "
        "ORDER BY record_id LIMIT ?", [sample_size]
    ).fetchall()
    gt_rows = con.execute(
        "SELECT record_id, signature_id FROM ground_truth WHERE record_id <= ?", [sample_size]
    ).fetchall()
    con.close()

    records = [{"record_id": r[0], "error_type": r[1], "message": r[2], "stack_trace": r[3]} for r in rows]
    ground_truth = {r[0]: r[1] for r in gt_rows}

    deterministic = attribute_batch(records)

    prompt = build_prompt(records)
    returncode, stdout, stderr = run_claude_p(prompt)
    (docs_dir / "claude_crosscheck_raw.txt").write_text(
        f"PROMPT:\n{prompt}\n\n---RETURNCODE {returncode}---\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}",
        encoding="utf-8",
    )
    claude_answers = parse_response(stdout)

    report_lines = [f"Live claude -p cross-check sample size: {len(records)}"]
    agree = 0
    for r in records:
        rid = r["record_id"]
        det_sid = deterministic[rid][0]
        claude_sid = claude_answers.get(rid)
        gt_sid = ground_truth.get(rid)
        matches_det = claude_sid == det_sid
        if matches_det:
            agree += 1
        report_lines.append(
            f"  record {rid}: ground_truth={gt_sid} deterministic={det_sid} claude={claude_sid} "
            f"claude_agrees_with_deterministic={matches_det}"
        )
    report_lines.append(f"Agreement rate (claude vs deterministic): {agree}/{len(records)}")
    (docs_dir / "claude_crosscheck_report.txt").write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/failures.duckdb"
    docs_dir = sys.argv[2] if len(sys.argv) > 2 else "docs"
    main(db_path, docs_dir)
