"""The 40 ground-truth DV regression-failure signatures for the silicon-DV extension.

5 signatures per block, 8 blocks (blocks.py) = 40, matching meta.json's claim exactly.
For each block, exactly 1 of its 5 signatures is "real": it describes the actual planted defect
(blocks.py's `defect_summary`) and is the only one of the 40 the simulator reproduction gate
(sim_repro_gate.py) can ever accept, because it is the only one with a real buggy/fixed RTL pair
behind it. The other 4 per block (32 of 40 total) are textual-pattern-only: a plausible DV log
line shape (UVM severity, assertion name, timeout, protocol check) with no backing simulation,
used to exercise clustering and attribution at the full 12,000-record scale. This mirrors this
repo's own existing 12-real/28-textual disclosure pattern one level down (12/40 there, 8/40 here,
disclosed, not padded).

Every signature carries its block's `testplan_id` for the real one and a distinct synthetic
testplan id for each textual one, read by testplan.md / dv_testplan_map.
"""

from __future__ import annotations

from dataclasses import dataclass

from .blocks import BLOCKS


@dataclass(frozen=True)
class Signature:
    sig_id: str
    block: str
    testplan_id: str
    real: bool
    template: str  # may contain {time}, {line}, {addr}, {val_a}, {val_b}, {cyc}


def _textual_templates_for(block: str) -> list[tuple[str, str]]:
    """Returns 4 (testplan_id, template) pairs of plausible-but-unbacked failure modes."""
    return [
        (
            f"{block.upper()}_ASSERTION_TIMING_0101",
            f"UVM_ERROR @ {{time}}ns: [tb_{block}] assertion Known_A failed: "
            f"unknown (X/Z) value observed on output at line {{line}}",
        ),
        (
            f"{block.upper()}_PROTOCOL_VIOLATION_0102",
            f"UVM_ERROR @ {{time}}ns: [tb_{block}] protocol violation: ready_i deasserted "
            f"while valid_o held high for {{cyc}} cycles (addr 0x{{addr}})",
        ),
        (
            f"{block.upper()}_RANDOMIZATION_FAILURE_0103",
            f"UVM_FATAL @ {{time}}ns: [tb_{block}] randomize() failed on class "
            f"{block}_seq_item after {{cyc}} constraint solver retries",
        ),
        (
            f"{block.upper()}_SCOREBOARD_TIMEOUT_0104",
            f"UVM_ERROR @ {{time}}ns: [tb_{block}] scoreboard timeout waiting for "
            f"response to transaction {{val_a}} after {{cyc}} cycles (last seen 0x{{addr}})",
        ),
    ]


def _build_signatures() -> list[Signature]:
    sigs: list[Signature] = []
    for i, block in enumerate(BLOCKS):
        real_template = (
            f"UVM_ERROR @ {{time}}ns: [tb_{block.name}] output mismatch: expected 0x{{val_a}} "
            f"got 0x{{val_b}} at line {{line}} ({block.defect_summary})"
        )
        sigs.append(
            Signature(
                sig_id=f"SIG{i * 5 + 1:02d}",
                block=block.name,
                testplan_id=block.testplan_id,
                real=True,
                template=real_template,
            )
        )
        for j, (testplan_id, template) in enumerate(_textual_templates_for(block.name)):
            sigs.append(
                Signature(
                    sig_id=f"SIG{i * 5 + 2 + j:02d}",
                    block=block.name,
                    testplan_id=testplan_id,
                    real=False,
                    template=template,
                )
            )
    return sigs


SIGNATURES: list[Signature] = _build_signatures()
SIGNATURES_BY_ID = {s.sig_id: s for s in SIGNATURES}

assert len(SIGNATURES) == 40
assert sum(1 for s in SIGNATURES if s.real) == 8
