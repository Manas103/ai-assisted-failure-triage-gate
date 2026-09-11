"""Signature 10: dedupe key collision bug.

dedupe_events keys on a timestamp rounded to the nearest minute, so
distinct events inside the same minute silently collide and only one
survives.
"""


def dedupe_events(events):
    seen = {}
    for e in events:
        rounded_minute = e["ts"] // 60  # BUG: coarser than the real identity
        seen[(e["event_id"], rounded_minute)] = e
    return list(seen.values())
