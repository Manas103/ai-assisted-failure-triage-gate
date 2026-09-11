"""Deterministic clustering of failure records into signatures.

Method: normalize each record's error_type + message + stack_trace by
stripping the volatile tokens generate_records.py injects (hex addresses,
build-id-shaped and other identifier-with-digits tokens, bare integers,
whitespace-only line differences), then group by the sha256 of the
normalized text. Two records that share a normalized template land in
the same cluster; this is deterministic (same input always produces the
same cluster id) and needs no training data or hyperparameters.

This is a template-hash clusterer, not a statistical/embedding one: it is
appropriate here because every record's noise is exactly the tokens the
generator injects, so a targeted regex strips it in one pass. A fuzzier
real-world corpus would need a softer similarity measure; that tradeoff
is stated in the README, not hidden.
"""

import hashlib
import re
from collections import Counter, defaultdict

_HEX_ADDR_RE = re.compile(r"0x[0-9a-fA-F]{6,16}")
_BUILD_ID_RE = re.compile(r"\bbuild-\d+\b")
_IDENT_DIGIT_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*_\d+\b")
_BARE_NUM_RE = re.compile(r"\d+")


def normalize(error_type, message, stack_trace):
    text = f"{error_type}\n{message}\n{stack_trace}"
    text = _HEX_ADDR_RE.sub("<ADDR>", text)
    text = _BUILD_ID_RE.sub("<BUILD>", text)
    text = _IDENT_DIGIT_RE.sub("<ID>", text)
    text = _BARE_NUM_RE.sub("<NUM>", text)
    return text


def template_key(error_type, message, stack_trace):
    normalized = normalize(error_type, message, stack_trace)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def cluster_records(records):
    """records: iterable of dicts with record_id, error_type, message,
    stack_trace. Returns dict cluster_key -> list of record_id."""
    clusters = defaultdict(list)
    for r in records:
        key = template_key(r["error_type"], r["message"], r["stack_trace"])
        clusters[key].append(r["record_id"])
    return dict(clusters)


def score_recovery(clusters, ground_truth, purity_threshold=0.95, coverage_threshold=0.95):
    """clusters: cluster_key -> [record_id]. ground_truth: record_id -> signature_id.

    A true signature counts as recovered if there is a single cluster
    that both (a) contains at least coverage_threshold of that
    signature's true records, and (b) is at least purity_threshold pure
    for that signature (few other signatures' records leaking in).
    Returns (recovered_count, per_signature_report).
    """
    sig_to_records = defaultdict(set)
    for rid, sid in ground_truth.items():
        sig_to_records[sid].add(rid)

    record_to_cluster = {}
    for ckey, rids in clusters.items():
        for rid in rids:
            record_to_cluster[rid] = ckey

    report = {}
    recovered = 0
    for sid, true_rids in sig_to_records.items():
        cluster_hits = Counter(record_to_cluster[rid] for rid in true_rids if rid in record_to_cluster)
        if not cluster_hits:
            report[sid] = {"recovered": False, "reason": "no records clustered"}
            continue
        best_cluster, best_count = cluster_hits.most_common(1)[0]
        coverage = best_count / len(true_rids)
        cluster_size = len(clusters[best_cluster])
        purity = best_count / cluster_size
        is_recovered = coverage >= coverage_threshold and purity >= purity_threshold
        if is_recovered:
            recovered += 1
        report[sid] = {
            "recovered": is_recovered,
            "best_cluster": best_cluster,
            "coverage": round(coverage, 4),
            "purity": round(purity, 4),
            "true_count": len(true_rids),
            "cluster_size": cluster_size,
        }
    return recovered, report
