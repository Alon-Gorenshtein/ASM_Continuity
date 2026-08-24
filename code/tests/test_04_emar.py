import pandas as pd
from lib.config import INTERMEDIATE
from lib.asm_vocab import ADMINISTERED_EVENT_TXT


def test_emar_administrations_present_for_eligible_subjects():
    emar = pd.read_parquet(INTERMEDIATE / "asm_emar.parquet")
    eligible = pd.read_parquet(INTERMEDIATE / "eligible_transitions.parquet")
    assert len(emar) > 5000
    assert emar["event_txt"].isin(ADMINISTERED_EVENT_TXT).sum() > 1000
    assert set(emar["subject_id"]) <= set(eligible["subject_id"])
