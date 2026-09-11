"""Signature 09: sort tie-break bug.

rank_candidates sorts only by score, ignoring the documented rule that
ties break by earlier submitted_at.
"""


def rank_candidates(candidates):
    # BUG: no secondary key, ties keep arbitrary/input order
    return sorted(candidates, key=lambda c: -c["score"])
