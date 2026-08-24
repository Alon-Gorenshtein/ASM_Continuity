import pandas as pd
from lib.config import INTERMEDIATE
from lib.asm_vocab import IV_AVAILABLE_DRUGS, ORAL_ONLY_DRUGS


def test_asm_orders_clean_and_classified():
    df = pd.read_parquet(INTERMEDIATE / "asm_orders.parquet")
    assert len(df) > 500
    assert set(df["canonical_drug"].unique()) <= (IV_AVAILABLE_DRUGS | ORAL_ONLY_DRUGS)
    assert not df["medication"].str.contains("alcohol withdrawal", case=False).any()
    assert not df["frequency"].fillna("").str.contains(r"\bPRN\b|\bONCE\b", case=False, regex=True).any()
    assert (df["expected_interval_hours"] > 0).all()
