import json
from lib.config import TABLES


def test_delay_duration_verified_values():
    with open(TABLES / "delay_duration.json") as f:
        out = json.load(f)

    all_g = out["all_gaps"]
    assert all_g["n"] == 251
    assert abs(all_g["median"] - 37.166666666666664) < 1e-6
    assert abs(all_g["iqr_low"] - 22.616666666666667) < 1e-6
    assert abs(all_g["iqr_high"] - 71.625) < 1e-6
    assert abs(all_g["p90"] - 143.01666666666668) < 1e-6
    assert abs(all_g["max"] - 722.5) < 1e-6

    resumed = out["resumed_before_discharge"]
    assert resumed["n"] == 221
    assert abs(resumed["median"] - 36.38333333333333) < 1e-6
    assert abs(resumed["iqr_low"] - 22.4) < 1e-6
    assert abs(resumed["iqr_high"] - 64.5) < 1e-6
    assert abs(resumed["p90"] - 131.93333333333334) < 1e-6

    not_resumed = out["not_resumed_before_discharge"]
    assert not_resumed["n"] == 30
    assert abs(not_resumed["median"] - 61.86666666666667) < 1e-6
    assert abs(not_resumed["iqr_low"] - 33.375) < 1e-6
    assert abs(not_resumed["iqr_high"] - 130.32916666666665) < 1e-6
    assert abs(not_resumed["p90"] - 185.66500000000002) < 1e-6
    assert abs(not_resumed["max"] - 477.3666666666667) < 1e-6

    by_interval = out["by_dosing_interval"]
    assert by_interval["6.0"]["n"] == 42
    assert by_interval["6.0"]["n_gap"] == 7
    assert by_interval["8.0"]["n"] == 201
    assert by_interval["8.0"]["n_gap"] == 56
    assert abs(by_interval["8.0"]["rate"] - 0.27860696517412936) < 1e-9
    assert by_interval["12.0"]["n"] == 1844
    assert by_interval["12.0"]["n_gap"] == 158
    assert by_interval["24.0"]["n"] == 382
    assert by_interval["24.0"]["n_gap"] == 30
    for k in by_interval:
        assert by_interval[k]["ci_low"] <= by_interval[k]["rate"] <= by_interval[k]["ci_high"]


def test_excess_beyond_expected_verified_values():
    with open(TABLES / "delay_duration.json") as f:
        d = json.load(f)
    ex = d["excess_beyond_expected"]
    assert ex["all_gaps"]["n"] == 251
    assert ex["all_gaps"]["median"] == 24.15
    assert ex["all_gaps"]["iqr_low"] == 10.5
    assert ex["all_gaps"]["iqr_high"] == 58.74166666666667
    assert ex["all_gaps"]["p90"] == 131.01666666666668
    assert ex["all_gaps"]["max"] == 710.5
    assert ex["resumed_before_discharge"]["n"] == 221
    assert ex["resumed_before_discharge"]["median"] == 23.78333333333333
    assert ex["not_resumed_before_discharge"]["n"] == 30
    assert ex["not_resumed_before_discharge"]["median"] == 51.93333333333334
