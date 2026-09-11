"""Generate 4,000 synthetic CI/production failure records across the 40
ground-truth signatures and store them in DuckDB.

Determinism: everything is driven by a single seeded random.Random so a
rerun with the same seed reproduces byte-identical records. Ground truth
(which signature actually produced each record) is stored in a separate
table; clustering and attribution never read it, only the scoring code
does, at the end.
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import duckdb

from triage.signatures import ALL_SIGNATURES

SEED = 20260911
N_RECORDS = 4000
TODAY = datetime(2026, 9, 11, 9, 0, 0)

_ID_WORDS = [
    "user", "order", "session", "batch", "worker", "shard", "conn",
    "cache", "queue", "req", "tenant", "job", "partition", "node",
    "customer", "invoice", "ticket", "device", "stream", "channel",
]


def _fill_message(rng, template):
    return template.format(
        id=f"{rng.choice(_ID_WORDS)}_{rng.randint(1000, 999999)}",
        num=rng.randint(1, 998),
    )


def _render_record(rng, sig):
    dispatch_line = rng.randint(80, 640)
    line_jitter = rng.randint(-3, 3)
    frame_line = max(1, sig["base_line"] + line_jitter)
    addr_hex = "".join(rng.choice("0123456789abcdef") for _ in range(12))
    message = _fill_message(rng, sig["message_template"])
    stack_trace = (
        "Traceback (most recent call last):\n"
        f"  File \"runtime/dispatch.py\", line {dispatch_line}, in _invoke\n"
        f"    return handler(*args, **kwargs)  # frame@0x{addr_hex}\n"
        f"  File \"{sig['file']}\", line {frame_line}, in {sig['function']}\n"
        f"    raise {sig['error_type']}(msg)\n"
        f"{sig['error_type']}: {message}"
    )
    minutes_ago = rng.randint(0, 90 * 24 * 60)
    ts = TODAY - timedelta(minutes=minutes_ago)
    build_id = f"build-{rng.randint(4000, 9999)}"
    return {
        "timestamp": ts,
        "build_id": build_id,
        "error_type": sig["error_type"],
        "message": message,
        "stack_trace": stack_trace,
    }


def generate(seed=SEED, n_records=N_RECORDS):
    rng = random.Random(seed)
    ids = [s["id"] for s in ALL_SIGNATURES]
    weights = [s["weight"] for s in ALL_SIGNATURES]
    chosen = rng.choices(ids, weights=weights, k=n_records)

    by_id = {s["id"]: s for s in ALL_SIGNATURES}
    records = []
    for i, sig_id in enumerate(chosen, start=1):
        sig = by_id[sig_id]
        rec = _render_record(rng, sig)
        rec["record_id"] = i
        rec["signature_id"] = sig_id
        records.append(rec)
    return records


def write_duckdb(records, db_path):
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("DROP TABLE IF EXISTS failure_records")
    con.execute("DROP TABLE IF EXISTS ground_truth")
    con.execute("""
        CREATE TABLE failure_records (
            record_id INTEGER PRIMARY KEY,
            timestamp TIMESTAMP,
            build_id VARCHAR,
            error_type VARCHAR,
            message VARCHAR,
            stack_trace VARCHAR
        )
    """)
    con.execute("""
        CREATE TABLE ground_truth (
            record_id INTEGER PRIMARY KEY,
            signature_id INTEGER
        )
    """)
    con.executemany(
        "INSERT INTO failure_records VALUES (?, ?, ?, ?, ?, ?)",
        [(r["record_id"], r["timestamp"], r["build_id"], r["error_type"],
          r["message"], r["stack_trace"]) for r in records],
    )
    con.executemany(
        "INSERT INTO ground_truth VALUES (?, ?)",
        [(r["record_id"], r["signature_id"]) for r in records],
    )
    con.close()


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/failures.duckdb"
    recs = generate()
    write_duckdb(recs, db_path)
    print(f"wrote {len(recs)} records to {db_path}")
