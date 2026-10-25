from triage.dv.blocks import BLOCKS
from triage.dv.dv_signatures import SIGNATURES


def test_forty_signatures_eight_blocks():
    assert len(SIGNATURES) == 40
    assert len(BLOCKS) == 8


def test_exactly_one_real_signature_per_block():
    for block in BLOCKS:
        real_for_block = [s for s in SIGNATURES if s.block == block.name and s.real]
        assert len(real_for_block) == 1
        assert real_for_block[0].testplan_id == block.testplan_id


def test_sig_ids_and_testplan_ids_unique():
    sig_ids = [s.sig_id for s in SIGNATURES]
    testplan_ids = [s.testplan_id for s in SIGNATURES]
    assert len(sig_ids) == len(set(sig_ids))
    assert len(testplan_ids) == len(set(testplan_ids))
