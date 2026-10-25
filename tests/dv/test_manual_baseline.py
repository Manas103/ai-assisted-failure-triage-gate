from triage.dv.cluster_attribute import build_reference_trigrams
from triage.dv.generate_dv_records import generate_records
from triage.dv.manual_baseline import manual_triage_one, tool_assisted_one


def test_tool_assisted_is_real_and_faster_than_manual_stand_in():
    recs = generate_records()[:10]
    ref = build_reference_trigrams()
    manual_results = [manual_triage_one(r) for r in recs]
    tool_results = [tool_assisted_one(r, ref) for r in recs]

    assert all(r.elapsed_s >= 0 for r in manual_results)
    assert all(r.elapsed_s >= 0 for r in tool_results)

    manual_median = sorted(r.elapsed_s for r in manual_results)[len(manual_results) // 2]
    tool_median = sorted(r.elapsed_s for r in tool_results)[len(tool_results) // 2]
    # The manual stand-in does an unindexed O(40) edit-distance scan plus a disk re-read per
    # candidate; the tool path is a single precomputed-trigram lookup. It should be slower on
    # any machine, not by a specific factor (see docs/dv_measure_report.json for the measured
    # one on this machine).
    assert manual_median > tool_median
