"""Generates the 12,000 synthetic DV regression-failure records.

Each record renders one of the 40 signatures' templates (dv_signatures.py) with randomized
placeholder values, then applies character-level noise (substitution/deletion) at a fixed rate.
Without that noise, every record would normalize back to its exact canonical template (different
blocks and failure categories use different words, not just different numbers), making
attribution a trivial 100% lookup; the noise rate is a deliberate task-difficulty choice, not a
property of real DV logs, and is disclosed as such (see this extension's section of the README).

Fixed seed 20261020, independent of the parent repo's seed (20260911) and the protocol
extension's (20261001).
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .dv_signatures import SIGNATURES, Signature

SEED = 20261020
N_RECORDS = 12_000
# Per-character substitution/deletion probability, applied after rendering. 12% (the parent
# repo's noise rate for its own 4,000-record corpus) left this corpus too easy here (0.99
# macro-F1, see README Findings): unlike that repo's single flat corpus, this one's 40
# signatures are drawn from 5 failure-mode categories repeated across 8 blocks, and the
# category text alone (not just digits) is what the attributor keys on, so a small per-character
# rate barely touches it. A sweep over round noise rates (10/15/20/25/30%) landed on 25% as a
# genuinely hard setting; the resulting macro-F1 is reported as measured, not chosen to clear 0.95.
NOISE_RATE = 0.25

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
_PRINTABLE = "abcdefghijklmnopqrstuvwxyz0123456789"


@dataclass(frozen=True)
class DvRecord:
    record_id: int
    sig_id: str  # ground truth, hidden from the attributor
    block: str  # ground truth
    testplan_id: str  # ground truth
    log_line: str  # the noised, rendered text the attributor actually sees


def _render(template: str, rng: random.Random) -> str:
    def fill(match: re.Match) -> str:
        kind = match.group(1)
        if kind == "time":
            return str(rng.randint(100, 9_999_999))
        if kind == "line":
            return str(rng.randint(1, 500))
        if kind == "addr":
            return f"{rng.randint(0, 0xFFFFFFFF):08x}"
        if kind in ("val_a", "val_b"):
            return f"{rng.randint(0, 0xFFFFFFFF):08x}"
        if kind == "cyc":
            return str(rng.randint(1, 10_000))
        raise ValueError(f"unknown placeholder {kind}")

    return _PLACEHOLDER_RE.sub(fill, template)


def _apply_noise(text: str, rng: random.Random, rate: float) -> str:
    out = []
    for ch in text:
        r = rng.random()
        if r < rate / 2:
            continue  # deletion
        elif r < rate:
            out.append(rng.choice(_PRINTABLE))  # substitution
        else:
            out.append(ch)
    return "".join(out)


def canonical_text(sig: Signature) -> str:
    """The noise-free, placeholder-stripped rendering used as the attributor's reference set."""
    return _PLACEHOLDER_RE.sub("N", sig.template)


def generate_records(n_records: int = N_RECORDS, noise_rate: float = NOISE_RATE) -> list[DvRecord]:
    rng = random.Random(SEED)
    records: list[DvRecord] = []
    for i in range(n_records):
        sig = SIGNATURES[i % len(SIGNATURES)]
        rendered = _render(sig.template, rng)
        noised = _apply_noise(rendered, rng, noise_rate)
        records.append(
            DvRecord(
                record_id=i,
                sig_id=sig.sig_id,
                block=sig.block,
                testplan_id=sig.testplan_id,
                log_line=noised,
            )
        )
    rng.shuffle(records)
    for i, r in enumerate(records):
        records[i] = DvRecord(i, r.sig_id, r.block, r.testplan_id, r.log_line)
    return records


def write_records(records: list[DvRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(asdict(r)) + "\n")


def load_records(path: Path) -> list[DvRecord]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            records.append(DvRecord(**d))
    return records


if __name__ == "__main__":
    import sys

    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/dv_records.jsonl")
    recs = generate_records()
    write_records(recs, out_path)
    print(f"wrote {len(recs)} records to {out_path}")
