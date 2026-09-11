"""Signature 08: unicode/byte-length truncation bug.

truncate_message slices by character count, not by encoded byte length,
so multi-byte characters push the result over the caller's byte budget.
"""


def truncate_message(msg, max_bytes):
    return msg[:max_bytes]  # BUG: character count, not byte length
