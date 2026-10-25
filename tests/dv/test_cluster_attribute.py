from triage.dv.cluster_attribute import accuracy, attribute_all, macro_f1
from triage.dv.generate_dv_records import generate_records


def test_macro_f1_above_floor_on_full_corpus():
    recs = generate_records()
    atts = attribute_all(recs)
    f1, per_class = macro_f1(recs, atts)
    acc = accuracy(recs, atts)
    assert len(per_class) == 40
    # Measured on this machine at the chosen 25% noise rate: macro-F1 ~0.9467, accuracy ~0.9461
    # (see docs/dv_measure_report.json). A generous floor here just guards against a real
    # regression, not against the exact measured value drifting slightly between runs.
    assert f1 > 0.85
    assert acc > 0.85


def test_attribution_predicts_a_real_signature():
    recs = generate_records()
    atts = attribute_all(recs)
    for a in atts[:50]:
        assert a.predicted_sig_id.startswith("SIG")
