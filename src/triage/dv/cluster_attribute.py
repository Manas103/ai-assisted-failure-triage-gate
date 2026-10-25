"""Deterministic attribution of a noised DV log line to (block, DV testplan entry).

Matches generate_dv_records.py's protocol-layer sibling pattern (deterministic_router.py):
character-trigram Jaccard similarity against each of the 40 canonical, placeholder-stripped
signature templates, not exact-substring matching, because at this extension's 12% per-character
noise rate an exact anchor phrase is unlikely to survive unscathed end to end. The predicted
signature's (block, testplan_id) pair is the actual attribution; macro-F1 is computed over the
40-way signature classification, which is a stricter (and lower) number than block-only or
testplan-only accuracy would be.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dv_signatures import SIGNATURES, Signature
from .generate_dv_records import DvRecord, canonical_text


def _trigrams(s: str) -> set[str]:
    s = s.lower()
    if len(s) < 3:
        return {s}
    return {s[i : i + 3] for i in range(len(s) - 2)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass(frozen=True)
class Attribution:
    record_id: int
    predicted_sig_id: str
    predicted_block: str
    predicted_testplan_id: str
    score: float


def build_reference_trigrams() -> dict[str, set[str]]:
    return {sig.sig_id: _trigrams(canonical_text(sig)) for sig in SIGNATURES}


def attribute_record(log_line: str, reference_trigrams: dict[str, set[str]]) -> Attribution:
    rec_trigrams = _trigrams(log_line)
    best_sig_id = None
    best_score = -1.0
    for sig_id, ref_trigrams in reference_trigrams.items():
        score = _jaccard(rec_trigrams, ref_trigrams)
        if score > best_score:
            best_score = score
            best_sig_id = sig_id
    sig = next(s for s in SIGNATURES if s.sig_id == best_sig_id)
    return Attribution(
        record_id=-1,
        predicted_sig_id=sig.sig_id,
        predicted_block=sig.block,
        predicted_testplan_id=sig.testplan_id,
        score=best_score,
    )


def attribute_all(records: list[DvRecord]) -> list[Attribution]:
    ref = build_reference_trigrams()
    out = []
    for r in records:
        a = attribute_record(r.log_line, ref)
        out.append(
            Attribution(
                record_id=r.record_id,
                predicted_sig_id=a.predicted_sig_id,
                predicted_block=a.predicted_block,
                predicted_testplan_id=a.predicted_testplan_id,
                score=a.score,
            )
        )
    return out


def macro_f1(records: list[DvRecord], attributions: list[Attribution]) -> tuple[float, dict]:
    """Macro-F1 over the 40-way signature classification (ground truth sig_id vs predicted)."""
    sig_ids = [s.sig_id for s in SIGNATURES]
    tp = {s: 0 for s in sig_ids}
    fp = {s: 0 for s in sig_ids}
    fn = {s: 0 for s in sig_ids}

    for rec, att in zip(records, attributions):
        if rec.sig_id == att.predicted_sig_id:
            tp[rec.sig_id] += 1
        else:
            fn[rec.sig_id] += 1
            fp[att.predicted_sig_id] += 1

    f1_per_class = {}
    for s in sig_ids:
        precision = tp[s] / (tp[s] + fp[s]) if (tp[s] + fp[s]) > 0 else 0.0
        recall = tp[s] / (tp[s] + fn[s]) if (tp[s] + fn[s]) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_per_class[s] = f1

    macro = sum(f1_per_class.values()) / len(f1_per_class)
    return macro, f1_per_class


def accuracy(records: list[DvRecord], attributions: list[Attribution]) -> float:
    correct = sum(1 for r, a in zip(records, attributions) if r.sig_id == a.predicted_sig_id)
    return correct / len(records)
