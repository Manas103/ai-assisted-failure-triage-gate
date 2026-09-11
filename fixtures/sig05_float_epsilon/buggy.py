"""Signature 05: floating point epsilon comparison bug.

is_close_enough uses exact equality on floats instead of a tolerance
band, so results that differ only by floating point rounding compare
unequal.
"""


def is_close_enough(a, b, tol=1e-6):
    return a == b  # BUG: exact equality, ignores tol
