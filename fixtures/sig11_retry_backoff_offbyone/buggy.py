"""Signature 11: retry-with-backoff off-by-one bug.

retry_with_backoff stops one attempt short of the documented
max_retries, so a call that would have succeeded on the last permitted
attempt raises instead.
"""


def retry_with_backoff(fn, max_retries):
    attempts = 0
    last_exc = None
    while attempts < max_retries:  # BUG: should allow max_retries+1 tries
        attempts += 1
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - deliberately broad retry loop
            last_exc = exc
    raise last_exc
