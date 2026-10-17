"""Orchestrates the protocol-layer triage measurement: generate the 22,000
log corpus, train and evaluate the layer-attribution CNN, route every log
through the deterministic path to find the residue, escalate the residue
through retrieval, measure the token-cost ratio, and (optionally) run the
live claude -p citation-discipline cross-check. Writes docs/protocol_*.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")

from triage.protocol.deterministic_router import route  # noqa: E402
from triage.protocol.escalate import escalate_batch, has_citation_before_step  # noqa: E402
from triage.protocol.generate_protocol_logs import generate  # noqa: E402
from triage.protocol.layer_cnn import train_and_eval  # noqa: E402
from triage.protocol.retrieval import TfidfIndex  # noqa: E402
from triage.protocol.token_cost import measure as measure_token_cost  # noqa: E402


def main(docs_dir="docs", run_llm_crosscheck=True):
    docs_dir = Path(docs_dir)
    docs_dir.mkdir(exist_ok=True)

    records = generate()
    print(f"generated {len(records)} protocol logs")

    cnn_out = train_and_eval(records)
    print(f"layer CNN macro-F1: {cnn_out['macro_f1']:.4f} (n_test={cnn_out['n_test']})")

    routed = [route(r["message"]) for r in records]
    residue_records = [r for r, m in zip(records, routed) if not m["attributed"]]
    residue_frac = len(residue_records) / len(records)
    print(f"residue: {len(residue_records)}/{len(records)} = {residue_frac:.4f}")

    index = TfidfIndex()
    escalated = escalate_batch(residue_records, index)
    n_cited = sum(1 for v in escalated.values() if has_citation_before_step(v["step"]))
    print(f"escalated citation-before-step compliance (structural): {n_cited}/{len(escalated)}")

    cost = measure_token_cost(records, residue_records, routed, index)
    print(f"token cost ratio: {cost['cost_ratio']:.5f} (1/{cost['cost_reduction_factor']:.1f})")

    report = dict(
        n_logs=len(records),
        macro_f1=cnn_out["macro_f1"],
        n_train=cnn_out["n_train"], n_test=cnn_out["n_test"],
        residue_count=len(residue_records), residue_frac=residue_frac,
        escalated_count=len(escalated),
        escalated_citation_compliance=f"{n_cited}/{len(escalated)}",
        token_cost=cost,
    )
    with open(docs_dir / "protocol_measure_report.json", "w") as f:
        json.dump(report, f, indent=2)

    if run_llm_crosscheck:
        from triage.protocol.llm_crosscheck import main as crosscheck_main
        residue_messages = [r["message"] for r in residue_records]
        n_loose, n_sample, n_strict = crosscheck_main(residue_messages, docs_dir)
        report["llm_crosscheck"] = dict(
            cites_before_step_compliant=n_loose, strict_format_compliant=n_strict, sample_size=n_sample,
        )
        with open(docs_dir / "protocol_measure_report.json", "w") as f:
            json.dump(report, f, indent=2)

    print(json.dumps({k: v for k, v in report.items() if k != "token_cost"}, indent=2))
    return report


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--docs", default="docs")
    p.add_argument("--no-llm-crosscheck", action="store_true")
    args = p.parse_args()
    main(args.docs, run_llm_crosscheck=not args.no_llm_crosscheck)
