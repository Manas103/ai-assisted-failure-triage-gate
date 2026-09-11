"""Signature 11: retry-with-backoff off-by-one bug, fixed.

retry_with_backoff makes max_retries + 1 total attempts (the initial try
plus max_retries retries), matching the documented contract.
"""


def retry_with_backoff(fn, max_retries):
    attempts = 0
    last_exc = None
    while attempts <= max_retries:
        attempts += 1
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - deliberately broad retry loop
            last_exc = exc
    raise last_exc


def _flaky_twice():
    state = {"calls": 0}

    def fn():
        state["calls"] += 1
        if state["calls"] <= 2:
            raise RuntimeError("transient")
        return "ok"

    return fn


REPRO_CASES = [
    ((_flaky_twice(), 2), "ok"),
]

MUTANTS = [
    ("shift the loop bound back by one",
     "while attempts <= max_retries:", "while attempts < max_retries:"),
    ("increment attempts before the try instead of matching the bound",
     "while attempts <= max_retries:\n        attempts += 1\n        try:",
     "while attempts <= max_retries:\n        try:"),
]
