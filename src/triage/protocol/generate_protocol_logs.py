"""22,000 simulated multimode protocol log lines, labeled by the stack layer
responsible (PHY, MAC, RLC, RRC, NAS). Each layer has several message
templates with randomized numeric fields (seeded, fixed seed 20261001), the
same jittered-template pattern the top-level triage/generate_records.py
uses for its 4,000 CI/production records. These are invented log shapes
inspired by publicly described cellular protocol stack behavior, not real
captured logs, and no real 3GPP specification text is reproduced anywhere;
the "specification passages" cited later in this module are an
original, fictional in-repo corpus (see spec_corpus.py).
"""
import random

LAYERS = ["PHY", "MAC", "RLC", "RRC", "NAS"]
SEED = 20261001

# Each template gets a {} slot pattern filled by _fill(); spec_tags links a
# template to the fictional spec corpus passage ids most relevant to it,
# used only as ground truth for evaluating retrieval quality, never as the
# retrieval mechanism itself.
TEMPLATES = {
    "PHY": [
        ("RSRP measurement {rsrp} dBm on carrier {carrier}, below cell-select threshold", ["phy_rsrp"]),
        ("PHY sync loss on cell {cell}, re-sync attempt {n}", ["phy_sync"]),
        ("CRC failure on PDSCH subframe {n}, HARQ process {proc}", ["phy_crc"]),
        ("RF front-end AGC saturation detected, gain index {n}", ["phy_agc"]),
        ("SRS transmission power {power} dBm exceeds configured max on UE {ue}", ["phy_srs"]),
    ],
    "MAC": [
        ("HARQ NACK retransmission count {n} exceeded max on UE {ue}, process {proc}", ["mac_harq"]),
        ("MAC PDU scheduling conflict at TTI {n} on carrier {carrier}", ["mac_sched"]),
        ("Random access procedure failure, RA-RNTI 0x{hex}, attempt {n}", ["mac_rach"]),
        ("Buffer status report missing for logical channel {n} on UE {ue}", ["mac_bsr"]),
        ("MAC contention resolution timer expired, UE {ue}", ["mac_crt"]),
    ],
    "RLC": [
        ("RLC AM retransmission buffer overflow on bearer {bearer}, size {n}", ["rlc_buf"]),
        ("Sequence number gap detected, SN={n}, bearer {bearer}", ["rlc_sn"]),
        ("RLC reassembly timeout on bearer {bearer} after {n} ms", ["rlc_reasm"]),
        ("Poll retransmit timer expired, bearer {bearer}, poll count {n}", ["rlc_poll"]),
        ("RLC status report rejected, invalid NACK SN={n}", ["rlc_status"]),
    ],
    "RRC": [
        ("RRC connection reestablishment failure, cause={cause}, UE {ue}", ["rrc_reest"]),
        ("RRC reconfiguration timeout, UE {ue}, transaction {n}", ["rrc_reconfig"]),
        ("Security mode command rejected by UE {ue}, cause={cause}", ["rrc_sec"]),
        ("Measurement report parsing error, UE {ue}, field offset {n}", ["rrc_meas"]),
        ("RRC connection release with redirect, UE {ue}, target carrier {carrier}", ["rrc_release"]),
    ],
    "NAS": [
        ("NAS attach reject, EMM cause={cause}, UE {ue}", ["nas_attach"]),
        ("Authentication failure, EMM cause={cause}, UE {ue}, attempt {n}", ["nas_auth"]),
        ("Tracking area update rejected, cause={cause}, UE {ue}", ["nas_tau"]),
        ("PDN connectivity request timeout, UE {ue}, APN index {n}", ["nas_pdn"]),
        ("NAS security context mismatch detected, UE {ue}, sequence {n}", ["nas_sec"]),
    ],
}


def _fill(template, rng):
    return template.format(
        rsrp=-rng.randint(95, 140), carrier=rng.randint(1, 8), cell=rng.randint(100, 999),
        n=rng.randint(1, 5000), proc=rng.randint(0, 7), power=rng.randint(-10, 23),
        ue=f"0x{rng.randint(0, 0xFFFF):04X}", hex=f"{rng.randint(0, 0xFFFFFF):06X}",
        bearer=rng.randint(1, 10), cause=rng.randint(1, 30),
    )


def _corrupt(message, rng, rate=0.08):
    """Per-character substitution/deletion noise, simulating truncated or
    partially garbled log capture. Without this, the five layers' fixed
    vocabularies make attribution a trivial lookup (measured macro-F1 1.0
    on the clean version, see README Findings); this is what makes 0.94 a
    real number to land on rather than a floor the task cannot miss."""
    out = []
    for ch in message:
        r = rng.random()
        if r < rate * 0.4:
            continue  # drop
        elif r < rate:
            out.append(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789"))
        else:
            out.append(ch)
    return "".join(out)


def generate(n_logs=22000, seed=SEED, corrupt_rate=0.4):
    rng = random.Random(seed)
    per_layer = n_logs // len(LAYERS)
    records = []
    record_id = 0
    for layer in LAYERS:
        templates = TEMPLATES[layer]
        for _ in range(per_layer):
            template, spec_tags = rng.choice(templates)
            message = _fill(template, rng)
            if corrupt_rate > 0:
                message = _corrupt(message, rng, rate=corrupt_rate)
            records.append(dict(record_id=record_id, layer=layer, message=message, spec_tags=spec_tags))
            record_id += 1
    rng.shuffle(records)
    for i, r in enumerate(records):
        r["record_id"] = i
    return records


if __name__ == "__main__":
    recs = generate()
    print(f"generated {len(recs)} protocol logs across {len(LAYERS)} layers")
    from collections import Counter
    print(Counter(r["layer"] for r in recs))
