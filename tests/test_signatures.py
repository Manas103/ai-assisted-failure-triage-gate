from triage.signatures import ALL_SIGNATURES, REAL_SIGNATURES, TEXTUAL_SIGNATURES


def test_forty_signatures_total():
    assert len(ALL_SIGNATURES) == 40


def test_twelve_real_twenty_eight_textual():
    assert len(REAL_SIGNATURES) == 12
    assert len(TEXTUAL_SIGNATURES) == 28
    assert all(s["real_fixture"] for s in REAL_SIGNATURES)
    assert not any(s["real_fixture"] for s in TEXTUAL_SIGNATURES)


def test_ids_are_unique_and_contiguous_1_to_40():
    ids = sorted(s["id"] for s in ALL_SIGNATURES)
    assert ids == list(range(1, 41))


def test_real_signatures_have_target_function_and_module():
    for s in REAL_SIGNATURES:
        assert s["module"]
        assert s["target_function"]
