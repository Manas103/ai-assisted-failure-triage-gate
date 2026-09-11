"""Signature 10: dedupe key collision bug, fixed.

dedupe_events keys on the exact (event_id, ts) pair, so only genuinely
identical events collapse.
"""


def dedupe_events(events):
    seen = {}
    for e in events:
        seen[(e["event_id"], e["ts"])] = e
    return list(seen.values())


_EVENTS = [
    {"event_id": "e1", "ts": 1000},
    {"event_id": "e1", "ts": 1015},  # same event_id, same floor(ts/60) bucket as above, distinct ts
    {"event_id": "e2", "ts": 1000},
]

REPRO_CASES = [
    ((_EVENTS,), list(_EVENTS)),
]

MUTANTS = [
    ("round the timestamp again (reintroduce the collision)",
     "seen[(e[\"event_id\"], e[\"ts\"])] = e",
     "seen[(e[\"event_id\"], e[\"ts\"] // 60)] = e"),
    ("key only on event_id, drop ts entirely",
     "seen[(e[\"event_id\"], e[\"ts\"])] = e",
     "seen[e[\"event_id\"]] = e"),
]
