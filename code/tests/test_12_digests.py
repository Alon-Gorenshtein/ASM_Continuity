import json
from lib.config import PROJECT_ROOT


def test_digests_exist_and_are_consistent():
    with open(PROJECT_ROOT / "output" / "results_digest.json") as f:
        results = json.load(f)
    with open(PROJECT_ROOT / "output" / "stats_digest.json") as f:
        stats = json.load(f)
    assert results["cohort_flow"]["eligible_transitions"] > 0
    assert results["cohort_flow"]["not_evaluable_count"] == 12
    assert results["cohort_flow"]["analysis_dataset_rows"] == 2469
    assert results["headline"]["gap_rate"] == stats["descriptive_and_logistic"]["overall"]["rate"]
    assert "iv_oral_and_sensitivity" in stats
    assert "demographic_descriptive" in stats
    assert "transfer_vs_control" in stats
    assert results["headline"]["comparator_pre_control_p"] == stats["transfer_vs_control"]["pre_control"]["mcnemar_p"]


def test_digests_include_delay_duration_and_new_cohort_flow_counts():
    with open(PROJECT_ROOT / "output" / "results_digest.json") as f:
        results = json.load(f)
    with open(PROJECT_ROOT / "output" / "stats_digest.json") as f:
        stats = json.load(f)
    assert results["cohort_flow"]["drug_observations_before_dose_confirmation"] == 5690
    assert results["cohort_flow"]["analysis_dataset_subjects"] == 1335
    assert "delay_duration" in stats
    assert stats["delay_duration"]["all_gaps"]["n"] == 251
    assert stats["delay_duration"]["by_dosing_interval"]["8.0"]["n"] == 201


def test_digests_include_comparator_rate_diff_headline():
    with open(PROJECT_ROOT / "output" / "results_digest.json") as f:
        results = json.load(f)
    assert "comparator_pre_rate_diff" in results["headline"]
    assert "comparator_post_rate_diff" in results["headline"]
    assert results["headline"]["comparator_pre_rate_diff"] > 0.04
    assert results["headline"]["comparator_post_rate_diff"] > 0.04
