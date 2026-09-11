"""Signature 07: integer division truncation bug.

average_batch_size uses floor division, silently discarding the
fractional remainder that downstream capacity planning needs.
"""


def average_batch_size(total_items, batch_count):
    if batch_count == 0:
        raise ValueError("batch_count must be > 0")
    return total_items // batch_count  # BUG: truncates
