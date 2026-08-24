import pandas as pd
from lib.config import INTERMEDIATE


def test_control_intervals_verified_counts():
    df = pd.read_parquet(INTERMEDIATE / "control_intervals.parquet")
    assert len(df) == 2469
    assert int(df["pre_gap_flag"].notna().sum()) == 2247
    assert int(df["post_gap_flag"].notna().sum()) == 2356
    assert int((df["pre_gap_flag"].notna() | df["post_gap_flag"].notna()).sum()) == 2444


def test_control_intervals_has_clustering_keys():
    df = pd.read_parquet(INTERMEDIATE / "control_intervals.parquet")
    assert "hadm_id" in df.columns
    assert "subject_id" in df.columns
    assert df["hadm_id"].notna().all()
    assert df["subject_id"].notna().all()
    assert len(df) == 2469


def test_post_schedule_changed_matches_verified_counts():
    df = pd.read_parquet(INTERMEDIATE / "control_intervals.parquet")
    assert "post_schedule_changed" in df.columns
    checked = df["post_schedule_changed"].notna().sum()
    changed = int((df["post_schedule_changed"] == True).sum())
    unchanged = int((df["post_schedule_changed"] == False).sum())
    assert checked == 2300
    assert changed == 14
    assert unchanged == 2286


def test_control_intervals_threshold_2_0_verified_counts():
    df = pd.read_parquet(INTERMEDIATE / "control_intervals_threshold_2.0.parquet")
    assert len(df) == 2469
    assert int(df["pre_gap_flag"].notna().sum()) == 2247
    assert int(df["post_gap_flag"].notna().sum()) == 2356


def test_control_intervals_threshold_3_0_verified_counts():
    df = pd.read_parquet(INTERMEDIATE / "control_intervals_threshold_3.0.parquet")
    assert len(df) == 2469
    assert int(df["pre_gap_flag"].notna().sum()) == 2247
    assert int(df["post_gap_flag"].notna().sum()) == 2356
