"""The escalation path for residue logs the deterministic router could not
confidently attribute: retrieve the single best-matching passage from the
fictional spec corpus, then require the proposed next debugging step to
cite that passage's id and name before any recommendation text. The
citation requirement is enforced structurally (has_citation_before_step),
not just by convention.
"""
import re

from triage.protocol.retrieval import TfidfIndex

_CITE_RE = re.compile(r"^\[cites ([^(]+) \(([a-z_]+)\)\]")


def escalate_one(message, index):
    hit = index.top1(message)
    step = (
        f"[cites {hit['citation']} ({hit['passage_id']})] {hit['text']} "
        f"Recommended next step: investigate per the cited passage before further action."
    )
    return dict(passage_id=hit["passage_id"], citation=hit["citation"], score=hit["score"], step=step)


def escalate_batch(residue_records, index=None):
    index = index or TfidfIndex()
    return {r["record_id"]: escalate_one(r["message"], index) for r in residue_records}


def has_citation_before_step(step_text):
    """True only if the text opens with a citation tag naming both the
    human-readable citation and the passage id, before the word 'step'
    first appears."""
    m = _CITE_RE.match(step_text)
    if not m:
        return False
    step_word_pos = step_text.lower().find("step")
    return step_word_pos == -1 or m.end() <= step_word_pos
