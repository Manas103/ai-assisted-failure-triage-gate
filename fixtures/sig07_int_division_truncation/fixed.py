"""Signature 07: integer division truncation bug, fixed.

average_batch_size uses true division to preserve the fractional part.
"""


def average_batch_size(total_items, batch_count):
    if batch_count == 0:
        raise ValueError("batch_count must be > 0")
    return total_items / batch_count


REPRO_CASES = [
    ((7, 2), 3.5),
    ((10, 4), 2.5),
]

MUTANTS = [
    ("revert to floor division",
     "return total_items / batch_count", "return total_items // batch_count"),
    ("swap operands (batch_count / total_items)",
     "return total_items / batch_count", "return batch_count / total_items"),
]
