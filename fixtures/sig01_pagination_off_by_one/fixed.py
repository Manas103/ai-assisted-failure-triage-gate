"""Signature 01: pagination fencepost error, fixed.

page_slice returns the full page; the slice upper bound is exclusive so it
must equal page * page_size, not page * page_size - 1.
"""


def page_slice(items, page, page_size):
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")
    start = (page - 1) * page_size
    end = page * page_size
    return items[start:end]


# REPRO_CASES: (args, expected) pairs that discriminate buggy from fixed.
REPRO_CASES = [
    (([1, 2, 3, 4, 5], 1, 2), [1, 2]),
    (([1, 2, 3, 4, 5], 2, 2), [3, 4]),
    ((list(range(10)), 3, 3), [6, 7, 8]),
]

# MUTANTS: (description, find, replace) textual patches applied to this
# file's source to stand in for plausible variants of the same defect
# class (off-by-one / boundary errors), used by the mutation-kill gate.
MUTANTS = [
    ("shift end bound by one (reintroduce the fencepost bug)",
     "end = page * page_size\n", "end = page * page_size - 1\n"),
    ("shift start bound by one instead",
     "start = (page - 1) * page_size\n", "start = (page - 1) * page_size + 1\n"),
]
