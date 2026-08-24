import pandas as pd
from lib.config import INTERMEDIATE


def test_transitions_well_formed():
    df = pd.read_parquet(INTERMEDIATE / "icu_floor_transitions.parquet")
    assert len(df) > 1000
    assert df["stay_id"].is_unique
    assert (df["floor_intime"] == df["icu_outtime"]).all()
    assert not df["careunit"].str.contains("Intensive Care", case=False).any()
    assert not (df["careunit"] == "Coronary Care Unit (CCU)").any()
