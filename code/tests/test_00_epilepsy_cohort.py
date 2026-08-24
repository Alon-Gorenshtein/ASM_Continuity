import pandas as pd
from lib.config import INTERMEDIATE


def test_epilepsy_cohort_matches_verified_recon_counts():
    df = pd.read_parquet(INTERMEDIATE / "epilepsy_admissions.parquet")
    assert len(df) == 20332
    assert df["subject_id"].nunique() == 8968
    assert int(df["status_epilepticus"].sum()) == 973
    assert df["hadm_id"].is_unique
