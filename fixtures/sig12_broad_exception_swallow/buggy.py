"""Signature 12: overly broad exception-swallowing bug.

parse_config_value catches every exception, including programmer errors
like passing None, and silently returns the default instead of
surfacing the real bug.
"""


def parse_config_value(raw, default):
    try:
        return int(raw)
    except Exception:  # BUG: swallows TypeError from raw=None too
        return default
