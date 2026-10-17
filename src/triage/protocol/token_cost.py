"""Measures the real token-count ratio between two designs, using tiktoken's
cl100k_base encoding (a real tokenizer, not a word-count approximation):

  naive: send every one of the 22,000 logs to a model, each call carrying
  the full 25-passage spec library (so the model itself can search and
  cite), plus the log message.

  this project's design: the deterministic CNN + router (local inference,
  zero model tokens) handles the non-residue logs entirely; only the ~11%
  residue is sent to a model, and each of those calls carries just the
  single passage retrieval.py already narrowed to locally, not the whole
  library, plus the log message.

The claimed 1/40 ratio is a product of two independent effects (fewer
calls, and each call carrying 1 passage instead of 25), not either one
alone; this module measures the actual combined ratio rather than
asserting it.
"""
import tiktoken

from triage.protocol.spec_corpus import PASSAGES

ENCODING = "cl100k_base"

INSTRUCTION = (
    "You are a cellular protocol debugging assistant. Given a specification "
    "passage library and a log line, pick the single best-matching passage "
    "and propose one next debugging step, citing the passage before the step."
)


def _enc():
    return tiktoken.get_encoding(ENCODING)


def naive_prompt_tokens(message, enc):
    library = "\n".join(f"{pid} ({cite}): {text}" for pid, cite, text in PASSAGES)
    prompt = f"{INSTRUCTION}\n\nPassage library:\n{library}\n\nLog: {message}"
    return len(enc.encode(prompt))


def escalated_prompt_tokens(message, retrieved_passage_text, retrieved_citation, enc):
    prompt = (
        f"{INSTRUCTION}\n\nRetrieved passage ({retrieved_citation}): "
        f"{retrieved_passage_text}\n\nLog: {message}"
    )
    return len(enc.encode(prompt))


def measure(all_records, residue_records, router_matches, index):
    """all_records: every generated log. residue_records: the subset routed
    to escalation. router_matches: dict record_id -> deterministic_router.route()
    output (used only to label which were residue; not needed for the naive
    side, which by definition sends every log regardless of attribution)."""
    enc = _enc()

    sample_n = min(300, len(all_records))
    naive_sample = all_records[:sample_n]
    naive_tokens_per_log = [naive_prompt_tokens(r["message"], enc) for r in naive_sample]
    avg_naive = sum(naive_tokens_per_log) / len(naive_tokens_per_log)

    residue_sample = residue_records[:min(300, len(residue_records))] if residue_records else []
    escalated_tokens_per_log = []
    for r in residue_sample:
        hit = index.top1(r["message"])
        escalated_tokens_per_log.append(
            escalated_prompt_tokens(r["message"], hit["text"], hit["citation"], enc)
        )
    avg_escalated = (sum(escalated_tokens_per_log) / len(escalated_tokens_per_log)) if escalated_tokens_per_log else 0.0

    n_total = len(all_records)
    n_residue = len(residue_records)

    total_naive_tokens = avg_naive * n_total
    total_escalated_tokens = avg_escalated * n_residue
    ratio = total_escalated_tokens / total_naive_tokens if total_naive_tokens else 0.0

    return dict(
        n_total=n_total, n_residue=n_residue, residue_frac=n_residue / n_total,
        avg_naive_tokens_per_log=avg_naive, avg_escalated_tokens_per_log=avg_escalated,
        total_naive_tokens_extrapolated=total_naive_tokens,
        total_escalated_tokens_extrapolated=total_escalated_tokens,
        cost_ratio=ratio, cost_reduction_factor=(1.0 / ratio if ratio else float("inf")),
        encoding=ENCODING, sample_n_naive=len(naive_sample), sample_n_residue=len(residue_sample),
    )
