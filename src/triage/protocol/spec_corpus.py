"""A small, original, fictional specification-style passage corpus used for
retrieval grounding. These are NOT excerpts from any real 3GPP specification;
they are invented for this repo, numbered "Internal Debug Spec Sxx.y" to
make that unambiguous, and are the only thing the escalation path is allowed
to cite."""

PASSAGES = [
    ("phy_rsrp", "Internal Debug Spec S1.1",
     "RSRP samples below the cell-selection floor for 3 consecutive measurement "
     "periods indicate the UE should trigger a cell reselection evaluation rather "
     "than remain camped; verify the measurement gap configuration before assuming "
     "a radio fault."),
    ("phy_sync", "Internal Debug Spec S1.2",
     "Repeated PHY synchronization loss on a cell after successful initial sync "
     "usually traces to a PSS/SSS detection window misalignment introduced by a "
     "timing-advance update; check the most recent TA command before escalating "
     "to RF hardware."),
    ("phy_crc", "Internal Debug Spec S1.3",
     "A CRC failure on a single PDSCH transport block is expected under normal "
     "link conditions and is handled by HARQ; escalate only when the failure rate "
     "for a given HARQ process exceeds the configured redundancy-version budget."),
    ("phy_agc", "Internal Debug Spec S1.4",
     "AGC saturation at the RF front end after a cell handover suggests the gain "
     "table was not reset for the new cell's reference signal power; re-apply the "
     "target cell's AGC profile before further diagnosis."),
    ("phy_srs", "Internal Debug Spec S1.5",
     "An SRS transmission power report above the configured ceiling should be "
     "clipped at the UE; a report above ceiling at the network side points to a "
     "power-headroom table mismatch between UE capability and configured Pmax."),
    ("mac_harq", "Internal Debug Spec S2.1",
     "A HARQ NACK count approaching the maximum retransmissions for a process "
     "should trigger a modulation and coding scheme downgrade recommendation "
     "before the transport block is discarded, not after."),
    ("mac_sched", "Internal Debug Spec S2.2",
     "A scheduling conflict at a given TTI across two logical channels is a "
     "scheduler allocation bug, not a UE-side fault; collect the scheduler's "
     "allocation trace for the conflicting TTI before filing against the UE."),
    ("mac_rach", "Internal Debug Spec S2.3",
     "Repeated random access failures on the same RA-RNTI across backoff windows "
     "suggest a preamble collision storm; check the PRACH configuration density "
     "before assuming a coverage issue."),
    ("mac_bsr", "Internal Debug Spec S2.4",
     "A missing buffer status report for a logical channel that has pending data "
     "most often indicates the BSR prohibit timer has not yet expired; this is "
     "expected scheduling behavior, not a defect, unless the timer value itself "
     "is misconfigured."),
    ("mac_crt", "Internal Debug Spec S2.5",
     "A contention resolution timer expiry after a successful RACH response "
     "usually means the C-RNTI echoed in the response did not match the UE's "
     "own identity; verify the RACH response PDU's MAC subheader fields."),
    ("rlc_buf", "Internal Debug Spec S3.1",
     "RLC AM retransmission buffer overflow on a bearer under sustained poor "
     "radio conditions is the expected failure mode once the configured maximum "
     "retransmission count is reached; escalate the bearer's radio link failure "
     "timer configuration, not the buffer size."),
    ("rlc_sn", "Internal Debug Spec S3.2",
     "A sequence number gap in RLC AM should trigger a status report requesting "
     "retransmission of the missing PDU; a gap that persists across multiple "
     "status report cycles indicates the status report itself is being lost, "
     "not that the original PDU was."),
    ("rlc_reasm", "Internal Debug Spec S3.3",
     "RLC reassembly timeout most commonly indicates a missing final segment of "
     "a segmented SDU; check whether the segmentation info field on the last "
     "received segment was set correctly before suspecting a lower-layer drop."),
    ("rlc_poll", "Internal Debug Spec S3.4",
     "A poll retransmit timer expiry after repeated polls with no status report "
     "response should be treated as a radio link problem at the RLC layer, "
     "escalatable to RRC connection reestablishment if it recurs."),
    ("rlc_status", "Internal Debug Spec S3.5",
     "A rejected RLC status report citing an invalid NACK sequence number is "
     "expected when the sender's transmission window has already advanced past "
     "that sequence number; this is a stale-report case, not corruption."),
    ("rrc_reest", "Internal Debug Spec S4.1",
     "RRC connection reestablishment failures clustered around a specific cause "
     "value should be cross-referenced against the originating RLC layer's radio "
     "link failure trigger before treating this as an RRC-layer defect."),
    ("rrc_reconfig", "Internal Debug Spec S4.2",
     "An RRC reconfiguration timeout on a specific transaction usually means the "
     "UE never received the reconfiguration message rather than rejecting it; "
     "check the PDCP sequence number of the reconfiguration delivery attempt."),
    ("rrc_sec", "Internal Debug Spec S4.3",
     "A rejected security mode command most often indicates a key derivation "
     "mismatch between the UE and network's stored security context, not a "
     "protocol violation; verify the NAS security context was not reset "
     "asymmetrically."),
    ("rrc_meas", "Internal Debug Spec S4.4",
     "A measurement report parsing error at a specific field offset should be "
     "checked against the measurement configuration's report format version "
     "before assuming a malformed UE implementation."),
    ("rrc_release", "Internal Debug Spec S4.5",
     "An RRC connection release with redirect to a different carrier is normal "
     "load-balancing behavior; only escalate if the redirected carrier "
     "consistently fails to admit the UE afterward."),
    ("nas_attach", "Internal Debug Spec S5.1",
     "An NAS attach reject with a subscription-related cause value should be "
     "checked against the HSS/UDM subscription record before assuming a "
     "signaling defect in the attach procedure itself."),
    ("nas_auth", "Internal Debug Spec S5.2",
     "Repeated NAS authentication failures for the same UE across attempts "
     "usually indicate a USIM/AuC sequence number desynchronization, resolved by "
     "the standard re-synchronization procedure rather than a signaling fix."),
    ("nas_tau", "Internal Debug Spec S5.3",
     "A tracking area update rejection with an implicit-detach cause suggests "
     "the UE's context already expired at the network side; this is expected "
     "after prolonged inactivity and not itself a fault."),
    ("nas_pdn", "Internal Debug Spec S5.4",
     "A PDN connectivity request timeout should be checked against the "
     "serving gateway's session establishment latency before assuming the "
     "request itself was malformed or lost."),
    ("nas_sec", "Internal Debug Spec S5.5",
     "A NAS security context sequence mismatch after a UE power cycle is the "
     "expected trigger for context re-establishment, not evidence of replay or "
     "tampering, unless it recurs without an intervening power cycle."),
]

PASSAGE_IDS = [p[0] for p in PASSAGES]
