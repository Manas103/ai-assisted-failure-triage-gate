"""Signature 09: sort tie-break bug, fixed.

rank_candidates breaks ties on submitted_at ascending (earlier wins).
"""


def rank_candidates(candidates):
    return sorted(candidates, key=lambda c: (-c["score"], c["submitted_at"]))


_B = {"name": "b", "score": 5, "submitted_at": 2}
_A = {"name": "a", "score": 5, "submitted_at": 1}
_C = {"name": "c", "score": 9, "submitted_at": 5}

REPRO_CASES = [
    (([_B, _A, _C],), [_C, _A, _B]),
]

MUTANTS = [
    ("drop the secondary tie-break key",
     "return sorted(candidates, key=lambda c: (-c[\"score\"], c[\"submitted_at\"]))",
     "return sorted(candidates, key=lambda c: -c[\"score\"])"),
    ("reverse the tie-break direction",
     "c[\"submitted_at\"]))", "-c[\"submitted_at\"]))"),
]
