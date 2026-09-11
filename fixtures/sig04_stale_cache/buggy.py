"""Signature 04: stale-cache-invalidation bug.

get_or_compute never checks the TTL once a value is cached, so callers
keep receiving a stale value forever.
"""


def get_or_compute(cache, key, compute_fn, ttl, now):
    if key in cache:  # BUG: ignores ttl entirely
        return cache[key][0]
    value = compute_fn()
    cache[key] = (value, now)
    return value
