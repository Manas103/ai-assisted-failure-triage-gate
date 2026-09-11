"""Signature 02: timezone-naive comparison bug.

is_expired compares a naive "now" against a timezone-aware expiry, which
raises TypeError in real Python instead of returning a boolean.
"""

from datetime import datetime


def is_expired(expiry, now=None):
    if now is None:
        now = datetime.utcnow()  # BUG: naive, but expiry is tz-aware
    return now >= expiry
