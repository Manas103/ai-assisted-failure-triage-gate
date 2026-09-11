"""Signature 04: stale-cache-invalidation bug, fixed.

get_or_compute recomputes once the cached entry's age exceeds ttl.
"""


def get_or_compute(cache, key, compute_fn, ttl, now):
    if key in cache:
        value, stored_at = cache[key]
        if now - stored_at < ttl:
            return value
    value = compute_fn()
    cache[key] = (value, now)
    return value


REPRO_CASES = [
    (({}, "k", lambda: "fresh", 10, 0), "fresh"),
    (({"k": ("stale", 0)}, "k", lambda: "recomputed", 10, 100), "recomputed"),
]

MUTANTS = [
    ("drop the ttl comparison, cache forever again",
     "        if now - stored_at < ttl:\n            return value\n",
     "        return value\n"),
    ("flip the ttl comparison direction",
     "if now - stored_at < ttl:", "if now - stored_at > ttl:"),
]
