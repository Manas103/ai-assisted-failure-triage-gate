"""Signature 02: timezone-naive comparison bug, fixed.

is_expired normalizes both sides to timezone-aware UTC before comparing.
"""

from datetime import datetime, timezone


def is_expired(expiry, now=None):
    if now is None:
        now = datetime.now(timezone.utc)
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now >= expiry


# now is omitted so the function falls back to its internal default,
# which is exactly the code path the seeded bug lives in.
REPRO_CASES = [
    ((datetime(2020, 1, 1, tzinfo=timezone.utc),), True),
    ((datetime(2099, 1, 1, tzinfo=timezone.utc),), False),
]

MUTANTS = [
    ("drop the expiry tzinfo normalization",
     "    if expiry.tzinfo is None:\n        expiry = expiry.replace(tzinfo=timezone.utc)\n",
     ""),
    ("compare with reversed operator (< instead of >=)",
     "return now >= expiry", "return now < expiry"),
]
