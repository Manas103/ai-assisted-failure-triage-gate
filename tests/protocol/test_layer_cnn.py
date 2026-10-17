import sys

sys.path.insert(0, "src")
from triage.protocol.generate_protocol_logs import generate  # noqa: E402
from triage.protocol.layer_cnn import encode, train_and_eval  # noqa: E402


def test_encode_shape_and_range():
    arr = encode(["hello", "a longer message here"], max_len=32)
    assert arr.shape == (2, 32)
    assert arr.min() >= 0 and arr.max() < 128


def test_train_and_eval_smoke_on_small_corpus():
    """A fast, small-scale smoke test, not the 22,000-log / 0.94 macro-F1
    claim measurement itself (that is run once by measure_protocol.py and
    recorded in docs/protocol_measure_report.json)."""
    recs = generate(n_logs=4000)
    out = train_and_eval(recs, epochs=8)
    assert out["n_train"] + out["n_test"] == 4000
    assert 0.0 <= out["macro_f1"] <= 1.0
    assert out["macro_f1"] > 0.5  # much better than the 0.2 random-guess floor for 5 classes
