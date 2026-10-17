import sys

import pytest

sys.path.insert(0, "src")
from triage.protocol.retrieval import PgvectorIndex, TfidfIndex, pgvector_available  # noqa: E402
from triage.protocol.spec_corpus import PASSAGES  # noqa: E402


def test_tfidf_index_retrieves_the_right_passage_for_a_clean_message():
    index = TfidfIndex()
    # phy_rsrp's canonical passage talks about RSRP and cell selection.
    hit = index.top1("RSRP measurement -103 dBm on carrier 3, below cell-select threshold")
    assert hit["passage_id"] == "phy_rsrp"
    assert hit["score"] > 0.0


def test_all_passages_are_retrievable_as_their_own_best_match():
    index = TfidfIndex()
    correct = 0
    for pid, _citation, text in PASSAGES:
        hit = index.top1(text)
        correct += int(hit["passage_id"] == pid)
    assert correct == len(PASSAGES)  # a passage's own text must retrieve itself


@pytest.mark.skipif(not pgvector_available(), reason="PostgreSQL is not running as a service on this machine")
def test_pgvector_index_connects():
    PgvectorIndex()
