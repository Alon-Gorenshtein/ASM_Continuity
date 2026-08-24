import pandas as pd
from lib.config import INTERMEDIATE


def test_eligible_transitions_have_active_asm():
    eligible = pd.read_parquet(INTERMEDIATE / "eligible_transitions.parquet")
    active = pd.read_parquet(INTERMEDIATE / "active_asm_at_transition.parquet")
    assert len(eligible) > 1000
    assert set(eligible["stay_id"]) == set(active["stay_id"])
    assert set(eligible["stay_id"]) <= set(
        pd.read_parquet(INTERMEDIATE / "icu_floor_transitions.parquet")["stay_id"]
    )
