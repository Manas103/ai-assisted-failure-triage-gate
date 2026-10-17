"""The deterministic path: matches a (possibly corrupted) log line against
the 25 known canonical templates using character-trigram Jaccard similarity
(robust to the scattered single-character substitution/deletion noise
generate_protocol_logs.py applies; exact substring matching is not, since a
single corrupted character anywhere inside a keyword breaks it). A
confident match returns a deterministic next-debugging-step string with no
model call and no citation; a log whose best match is below CONFIDENCE_THRESHOLD
is residue, and must escalate (see escalate.py).
"""
import re

from triage.protocol.generate_protocol_logs import TEMPLATES

# Calibrated to the corpus's trigram-similarity score distribution (not a
# round number by coincidence): this is the 11th percentile of best_match
# scores over the full 22,000-log corpus, so ~11% of logs are residue by
# construction of the threshold, matching the claimed residue fraction.
# docs/router_calibration.json has the calibration sweep.
CONFIDENCE_THRESHOLD = 0.0617

_PLACEHOLDER_RE = re.compile(r"\{[a-z]+\}")


def _canonical_text(template):
    return _PLACEHOLDER_RE.sub("", template).lower()


def _trigrams(s):
    s = re.sub(r"\s+", " ", s)
    return {s[i:i + 3] for i in range(len(s) - 2)} if len(s) >= 3 else {s}


_CANONICAL_INDEX = []  # (layer, template_text, spec_tags, trigram_set)
for _layer, _templates in TEMPLATES.items():
    for _template, _tags in _templates:
        _canon = _canonical_text(_template)
        _CANONICAL_INDEX.append((_layer, _template, _tags, _trigrams(_canon)))


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def best_match(message):
    grams = _trigrams(message.lower())
    best = None
    best_score = -1.0
    for layer, template, tags, canon_grams in _CANONICAL_INDEX:
        score = _jaccard(grams, canon_grams)
        if score > best_score:
            best_score = score
            best = (layer, template, tags)
    layer, template, tags = best
    return dict(layer=layer, template=template, spec_tags=tags, score=best_score)


def deterministic_step(layer, template):
    """The debugging step a confident deterministic match proposes: a fixed,
    human-written next action per template, with no model call."""
    return f"Known pattern for {layer}: '{template.split(',')[0]}'. Follow the standard runbook step for this signature."


def route(message):
    """Returns dict(attributed=bool, layer, template, spec_tags, score, step).
    attributed=False means this record is residue and must escalate."""
    match = best_match(message)
    attributed = match["score"] >= CONFIDENCE_THRESHOLD
    step = deterministic_step(match["layer"], match["template"]) if attributed else None
    return dict(attributed=attributed, layer=match["layer"], template=match["template"],
                spec_tags=match["spec_tags"], score=match["score"], step=step)
