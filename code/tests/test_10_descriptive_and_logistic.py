import json
from lib.config import TABLES


def test_descriptive_and_logistic_output_shape():
    with open(TABLES / "descriptive_and_logistic.json") as f:
        out = json.load(f)
    assert 0 <= out["overall"]["rate"] <= 1
    assert out["overall"]["ci_low"] <= out["overall"]["rate"] <= out["overall"]["ci_high"]
    assert "iv_available" in out["by_drug_class"] or "oral_only" in out["by_drug_class"]
    predictors = {row["predictor"] for row in out["logistic_regression"]}
    # only the 6 pre-specified variables (one-hot expansion for categoricals) -- no demographic terms
    disallowed_prefixes = ("race_", "insurance_", "language_", "marital_status_")
    assert not any(p.startswith(disallowed_prefixes) for p in predictors)
    assert 5 <= len(out["logistic_regression"]) <= 10  # 6 vars, route_class/sex one-hot to 1 col each
    for row in out["logistic_regression"]:
        assert row["odds_ratio"] > 0
        assert 0 <= row["p_bh"] <= 1
