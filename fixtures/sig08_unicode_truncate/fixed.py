"""Signature 08: unicode/byte-length truncation bug, fixed.

truncate_message truncates the UTF-8 encoded bytes and decodes back,
dropping a trailing partial character rather than overflowing the
byte budget.
"""


def truncate_message(msg, max_bytes):
    encoded = msg.encode("utf-8")
    if len(encoded) <= max_bytes:
        return msg
    truncated = encoded[:max_bytes]
    while truncated:
        try:
            return truncated.decode("utf-8")
        except UnicodeDecodeError:
            truncated = truncated[:-1]
    return ""


REPRO_CASES = [
    (("hello", 3), "hel"),
    (("éééé", 3), "é"),
]

MUTANTS = [
    ("revert to character-count slicing",
     "    encoded = msg.encode(\"utf-8\")\n    if len(encoded) <= max_bytes:\n        return msg\n    truncated = encoded[:max_bytes]\n    while truncated:\n        try:\n            return truncated.decode(\"utf-8\")\n        except UnicodeDecodeError:\n            truncated = truncated[:-1]\n    return \"\"\n",
     "    return msg[:max_bytes]\n"),
    ("off-by-one the byte budget",
     "truncated = encoded[:max_bytes]", "truncated = encoded[:max_bytes + 1]"),
]
