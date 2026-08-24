import json
from lib.config import TABLES


def test_demographic_descriptive_output_shape():
    with open(TABLES / "demographic_descriptive.json") as f:
        out = json.load(f)
    for var in ("race_collapsed", "language_collapsed", "insurance", "marital_status"):
        assert var in out
        assert len(out[var]["categories"]) >= 2
        assert 0 <= out[var]["omnibus_p"] <= 1
        for cat_stats in out[var]["categories"].values():
            assert 0 <= cat_stats["rate"] <= 1
            assert cat_stats["ci_low"] <= cat_stats["rate"] <= cat_stats["ci_high"]
