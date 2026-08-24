import json
from lib.config import TABLES


def _load():
    with open(TABLES / "transfer_vs_control.json") as f:
        return json.load(f)


def test_transfer_vs_control_verified_values():
    out = _load()
    pre = out["pre_control"]
    assert pre["n"] == 2247
    assert abs(pre["transfer_gap_rate"] - 0.07521139296840232) < 1e-9
    assert abs(pre["control_gap_rate"] - 0.017356475300400534) < 1e-9
    assert pre["discordant_transfer_only"] == 163
    assert pre["discordant_control_only"] == 33
    assert pre["concordant_both"] == 6
    assert pre["concordant_neither"] == 2045
    assert pre["mcnemar_p"] < 1e-20

    post = out["post_control"]
    assert post["n"] == 2356
    assert abs(post["transfer_gap_rate"] - 0.08913412563667232) < 1e-9
    assert abs(post["control_gap_rate"] - 0.02504244482173175) < 1e-9
    assert post["discordant_transfer_only"] == 197
    assert post["discordant_control_only"] == 46
    assert post["concordant_both"] == 13
    assert post["concordant_neither"] == 2100
    assert post["mcnemar_p"] < 1e-20


def test_rate_diff_brackets_and_is_positive():
    d = _load()
    for key in ("pre_control", "post_control"):
        rd = d[key]["rate_diff"]
        lo_h, hi_h = d[key]["rate_diff_ci_hadm"]
        lo_s, hi_s = d[key]["rate_diff_ci_subject"]
        assert lo_h < rd < hi_h
        assert lo_s < rd < hi_s
        assert lo_h > 0 and lo_s > 0  # CI excludes zero -- the effect is large and positive
        assert rd > 0.04  # sanity floor well below both verified point estimates (0.0579, 0.0641)


def test_schedule_unchanged_sensitivity_matches_verified_counts():
    d = _load()
    su = d["post_control_schedule_unchanged"]
    assert su["n"] == 2286


def test_selection_check_matches_verified_counts():
    d = _load()
    sc = d["selection_check"]
    assert sc["pre"]["has_control"]["n"] == 2247
    assert sc["pre"]["has_control"]["n_gap"] == 169
    assert sc["pre"]["no_control"]["n"] == 222
    assert sc["pre"]["no_control"]["n_gap"] == 82
    assert sc["post"]["has_control"]["n"] == 2356
    assert sc["post"]["has_control"]["n_gap"] == 210
    assert sc["post"]["no_control"]["n"] == 113
    assert sc["post"]["no_control"]["n_gap"] == 41


def test_threshold_sensitivity_brackets():
    d = _load()
    ts = d["threshold_sensitivity"]
    assert set(ts.keys()) == {"2.0", "3.0"}
    for t in ("2.0", "3.0"):
        for label in ("pre_control", "post_control"):
            r = ts[t][label]
            assert 0 <= r["mcnemar_p"] <= 1
            assert r["rate_diff_ci_hadm"][0] <= r["rate_diff"] <= r["rate_diff_ci_hadm"][1]
            assert r["rate_diff_ci_subject"][0] <= r["rate_diff"] <= r["rate_diff_ci_subject"][1]
            assert -1 <= r["rate_diff"] <= 1
            assert r["n"] > 0


def test_threshold_sensitivity_n_matches_across_thresholds():
    d = _load()
    ts = d["threshold_sensitivity"]
    assert ts["3.0"]["pre_control"]["n"] == ts["2.0"]["pre_control"]["n"] == d["pre_control"]["n"]
    assert ts["3.0"]["post_control"]["n"] == ts["2.0"]["post_control"]["n"] == d["post_control"]["n"]
