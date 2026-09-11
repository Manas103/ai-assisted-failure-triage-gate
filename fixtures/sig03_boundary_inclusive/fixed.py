"""Signature 03: inclusive/exclusive boundary bug, fixed.

Both ranges are documented as inclusive on both ends, so the comparisons
must be <=, not <.
"""


def ranges_overlap(a_start, a_end, b_start, b_end):
    return a_start <= b_end and b_start <= a_end


REPRO_CASES = [
    ((1, 5, 5, 10), True),
    ((1, 5, 6, 10), False),
    ((10, 10, 10, 10), True),
]

MUTANTS = [
    ("flip both comparisons back to strict <",
     "return a_start <= b_end and b_start <= a_end",
     "return a_start < b_end and b_start < a_end"),
    ("swap the operands (a and b reversed on one side)",
     "return a_start <= b_end and b_start <= a_end",
     "return b_start <= b_end and a_start <= a_end"),
]
