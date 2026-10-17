"""A genuine claude -p cross-check on a small, disclosed live sample of
residue records: asks a real model to propose a next debugging step while
citing a spec passage, and checks whether it actually complies with the
citation-before-step requirement escalate.py enforces structurally. This is
not the mechanism the token-cost claim is measured on (that is the
deterministic retrieval in escalate.py, applied to every residue record);
it is a live spot-check of whether the citation discipline is something a
real model will actually follow when asked, mirroring the top-level
triage/llm_crosscheck.py precedent in this same repo.
"""
import json
import subprocess
from pathlib import Path

import re

from triage.protocol.escalate import has_citation_before_step
from triage.protocol.retrieval import TfidfIndex
from triage.protocol.spec_corpus import PASSAGES

SAMPLE_SIZE = 15
_LOOSE_CITE_RE = re.compile(r"^\[cites [^\]]+\]")


def loose_citation_before_step(text):
    """Same intent as escalate.has_citation_before_step, but accepts any
    passage-id spelling (not just the internal lowercase_tag format): used
    to separate "did it cite something before proposing a step at all" from
    "did it use our exact internal id format" (see README Findings)."""
    m = _LOOSE_CITE_RE.match(text)
    if not m:
        return False
    step_pos = text.lower().find("step")
    return step_pos == -1 or m.end() <= step_pos


def build_prompt(sample_messages, index):
    passage_lines = "\n".join(f"{pid} ({cite}): {text}" for pid, cite, text in PASSAGES)
    msg_lines = "\n".join(f"record_id={i}: {m}" for i, m in enumerate(sample_messages))
    return (
        "You are a cellular protocol debugging assistant. You are given a "
        "fixed library of specification passages and a list of residue log "
        "lines that a deterministic classifier could not confidently "
        "attribute. For each record, pick the single best-matching passage "
        "id from the library and propose ONE next debugging step. You MUST "
        "cite the passage id and name before the proposed step, in exactly "
        "this format: '[cites <citation> (<passage_id>)] <next step text>'. "
        "Respond with ONLY a JSON object mapping record_id (string) to the "
        "full formatted string, no prose, no markdown fences.\n\n"
        f"Passage library:\n{passage_lines}\n\nRecords:\n{msg_lines}"
    )


def run_claude_p(prompt, model="claude-haiku-4-5-20251001", timeout=120):
    proc = subprocess.run(
        ["claude", "-p", "--model", model, prompt],
        capture_output=True, text=True, timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def parse_response(stdout):
    text = stdout.strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        raw = json.loads(text[start:end + 1])
        out = {}
        for k, v in raw.items():
            k = str(k)
            if "=" in k:
                k = k.split("=", 1)[1]
            out[int(k)] = v
        return out
    except Exception:
        return {}


def main(residue_messages, docs_dir, sample_size=SAMPLE_SIZE):
    docs_dir = Path(docs_dir)
    sample = residue_messages[:sample_size]
    index = TfidfIndex()

    prompt = build_prompt(sample, index)
    returncode, stdout, stderr = run_claude_p(prompt)
    (docs_dir / "protocol_claude_crosscheck_raw.txt").write_text(
        f"PROMPT:\n{prompt}\n\n---RETURNCODE {returncode}---\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}",
        encoding="utf-8",
    )
    claude_answers = parse_response(stdout)

    report_lines = [f"Live claude -p citation-discipline cross-check, sample size: {len(sample)}"]
    n_strict, n_loose = 0, 0
    for i in range(len(sample)):
        answer = claude_answers.get(i, "")
        strict = has_citation_before_step(answer) if answer else False
        loose = loose_citation_before_step(answer) if answer else False
        n_strict += int(strict)
        n_loose += int(loose)
        report_lines.append(f"  record {i}: strict_format={strict} cites_before_step={loose} answer={answer!r}")
    report_lines.append(f"Strict internal-tag-id format compliance: {n_strict}/{len(sample)}")
    report_lines.append(f"Cites-something-before-step compliance (any id spelling): {n_loose}/{len(sample)}")
    (docs_dir / "protocol_claude_crosscheck_report.txt").write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))
    return n_loose, len(sample), n_strict
