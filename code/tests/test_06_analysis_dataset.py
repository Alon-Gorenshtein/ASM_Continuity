import pandas as pd
from lib.config import INTERMEDIATE


def test_analysis_dataset_complete():
    df = pd.read_parquet(INTERMEDIATE / "analysis_dataset.parquet")
    assert len(df) == 2469  # updated after the discharge-censoring fix (Task 2 of this plan)
    # count through the merge chain; a drift toward the pre-Task-7-fix 2,637 or any inflation from a
    # many-to-many merge should fail loudly, not slip past a loose lower bound.
    required = ["gap_flag", "route_class", "icu_los_days", "status_epilepticus",
                "polytherapy_count", "age", "sex"]
    for col in required:
        assert col in df.columns
        assert df[col].notna().mean() > 0.95, f"{col} has too many missing values"
    assert df["polytherapy_count"].min() >= 1


def test_analysis_dataset_evaluable_only_and_has_handoff_predictors():
    df = pd.read_parquet(INTERMEDIATE / "analysis_dataset.parquet")
    assert len(df) == 2469
    assert df["hadm_id"].nunique() == 1583
    for col in ["transfer_hour", "transfer_is_weekend", "source_icu_type", "destination_ward_type"]:
        assert col in df.columns
        assert df[col].notna().mean() > 0.95
    assert df["transfer_hour"].between(0, 23).all()
    assert set(df["destination_ward_type"].dropna().unique()) <= {"stepdown", "regular_floor"}
