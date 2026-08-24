import json
from lib.config import TABLES


def test_sensitivity_output_shape():
    with open(TABLES / "iv_oral_and_sensitivity.json") as f:
        out = json.load(f)
    assert 0 <= out["iv_vs_oral"]["cramers_v"] <= 1
    assert len(out["threshold_sensitivity"]) == 3
    assert 0 <= out["clustering_sensitivity"]["gap_rate"] <= 1


def test_threshold_sensitivity_has_cis_and_switch_exclusion_present():
    with open(TABLES / "iv_oral_and_sensitivity.json") as f:
        out = json.load(f)
    for entry in out["threshold_sensitivity"]:
        assert "ci_low" in entry and "ci_high" in entry
        assert entry["ci_low"] <= entry["gap_rate"] <= entry["ci_high"]
    swe = out["switch_excluded_sensitivity"]
    assert swe["n_excluded"] > 0
    assert 0 <= swe["gap_rate"] <= 1
    assert swe["ci_low"] <= swe["gap_rate"] <= swe["ci_high"]
    assert "levetiracetam" in out["by_drug"]
    for drug_stats in out["by_drug"].values():
        assert drug_stats["ci_low"] <= drug_stats["rate"] <= drug_stats["ci_high"]


def test_iv_vs_oral_has_cluster_adjusted_rate_diff():
    with open(TABLES / "iv_oral_and_sensitivity.json") as f:
        out = json.load(f)
    ivo = out["iv_vs_oral"]
    # naive chi-square fields still present, unchanged
    assert "chi2" in ivo and "cramers_v" in ivo
    # new cluster-adjusted fields present and internally consistent
    for key in ("rate_diff", "rate_diff_ci_low", "rate_diff_ci_high", "rate_diff_bootstrap_p"):
        assert key in ivo
    assert ivo["rate_diff_ci_low"] <= ivo["rate_diff"] <= ivo["rate_diff_ci_high"]
    assert 0 <= ivo["rate_diff_bootstrap_p"] <= 1
    assert -1.0 <= ivo["rate_diff"] <= 1.0
