"""Signature 05: floating point epsilon comparison bug, fixed.

is_close_enough compares within an absolute tolerance band.
"""


def is_close_enough(a, b, tol=1e-6):
    return abs(a - b) <= tol


REPRO_CASES = [
    ((0.1 + 0.2, 0.3, 1e-9), True),
    ((1.0, 1.2, 1e-9), False),
]

MUTANTS = [
    ("flip the comparison operator (< instead of <=)",
     "return abs(a - b) <= tol", "return abs(a - b) < tol and False"),
    ("drop abs(), compare raw signed difference",
     "return abs(a - b) <= tol", "return (a - b) <= tol"),
]
