"""Signature 03: inclusive/exclusive boundary bug in a range-overlap check.

ranges_overlap treats the documented inclusive bounds as exclusive, so two
ranges that only touch at a shared endpoint are wrongly reported as
non-overlapping.
"""


def ranges_overlap(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end  # BUG: should be <=
