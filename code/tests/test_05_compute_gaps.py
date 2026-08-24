import pandas as pd
from lib.config import INTERMEDIATE


def test_gap_files_written_for_all_thresholds():
    for t in ("1.5", "2.0", "3.0"):
        df = pd.read_parquet(INTERMEDIATE / f"gaps_threshold_{t}.parquet")
        assert len(df) > 500
        assert df["gap_hours"].dropna().ge(0).all()


def test_evaluable_count_matches_verified_value():
    for t in ("1.5", "2.0", "3.0"):
        df = pd.read_parquet(INTERMEDIATE / f"gaps_threshold_{t}.parquet")
        assert int((~df["evaluable"]).sum()) == 12
        assert int(df["evaluable"].sum()) == 2469
