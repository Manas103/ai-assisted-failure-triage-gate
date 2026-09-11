"""Deterministic root-cause attribution: assign a signature id to a single
failure record.

This is intentionally a separate mechanism from cluster.py, not a
relabeling of its clusters: a real triage system has a curated signature
library (built once, offline, by whoever defined the 40 signatures) and
attributes each new record against that library independently of however
records happen to batch together. attribute_record here does exactly
that: it builds one canonical, noise-free rendering of every signature's
template at import time, normalizes it with the same normalize() used for
clustering, and matches new records against that fixed library.

Two-stage match:
  1. Exact match on the normalized text against the canonical library.
  2. Fallback: token-Jaccard nearest neighbor against the library, for any
     record whose normalization does not land exactly on a known
     template (kept deterministic: ties broken by lowest signature id).
"""

from triage.cluster import normalize
from triage.signatures import ALL_SIGNATURES


def _canonical_stack_trace(sig):
    return (
        "Traceback (most recent call last):\n"
        "  File \"runtime/dispatch.py\", line 0, in _invoke\n"
        "    return handler(*args, **kwargs)  # frame@0x000000000000\n"
        f"  File \"{sig['file']}\", line {sig['base_line']}, in {sig['function']}\n"
        f"    raise {sig['error_type']}(msg)\n"
        f"{sig['error_type']}: {sig['message_template'].format(id='id_0', num=0)}"
    )


def _build_library():
    library = {}
    for sig in ALL_SIGNATURES:
        key = normalize(sig["error_type"], sig["message_template"].format(id="id_0", num=0),
                         _canonical_stack_trace(sig))
        library.setdefault(key, sig["id"])
    return library


_LIBRARY = _build_library()
_LIBRARY_TOKENS = {key: frozenset(key.split()) for key in _LIBRARY}


def _jaccard(a, b):
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def attribute_record(error_type, message, stack_trace):
    """Returns (signature_id, method) where method is 'exact' or 'nearest'."""
    key = normalize(error_type, message, stack_trace)
    if key in _LIBRARY:
        return _LIBRARY[key], "exact"

    tokens = frozenset(key.split())
    best_sig_id, best_score = None, -1.0
    for lib_key, sig_id in sorted(_LIBRARY.items(), key=lambda kv: kv[1]):
        score = _jaccard(tokens, _LIBRARY_TOKENS[lib_key])
        if score > best_score:
            best_score = score
            best_sig_id = sig_id
    return best_sig_id, "nearest"


def attribute_batch(records):
    """records: iterable of dicts with record_id, error_type, message,
    stack_trace. Returns dict record_id -> (signature_id, method)."""
    return {
        r["record_id"]: attribute_record(r["error_type"], r["message"], r["stack_trace"])
        for r in records
    }


def score_accuracy(attributions, ground_truth):
    total = len(ground_truth)
    correct = sum(
        1 for rid, sid in ground_truth.items()
        if rid in attributions and attributions[rid][0] == sid
    )
    return correct, total, (correct / total if total else 0.0)
