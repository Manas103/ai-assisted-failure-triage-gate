"""Signature 12: overly broad exception-swallowing bug, fixed.

parse_config_value only swallows the expected ValueError (a malformed
but present value); a wrong type such as raw=None re-raises so the real
caller bug is not hidden.
"""


def parse_config_value(raw, default):
    try:
        return int(raw)
    except ValueError:
        return default


# A REPRO_CASES expected value of the form "RAISES:<ExceptionClassName>"
# means the call is expected to raise that exception type rather than
# return a value; the generic gate runner (repro_gate.py) understands
# this convention for every fixture, not just this one.
REPRO_CASES = [
    (("42", 0), 42),
    (("not-a-number", 0), 0),
    ((None, 0), "RAISES:TypeError"),
]

MUTANTS = [
    ("widen back to bare except",
     "except ValueError:", "except Exception:"),
    ("swallow TypeError too",
     "except ValueError:", "except (ValueError, TypeError):"),
]
