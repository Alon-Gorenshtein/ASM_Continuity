"""Keep only ICU-to-floor transitions where >=1 ASM order was active exactly at the ICU-departure
instant. Scouting recon (a quicker, independent join done during idea selection) found ~4,211
transitions / ~3,784 admissions -- treated here as a sanity ballpark, not a hard target, since this
script's eligibility logic may legitimately differ in minor ways.
"""
import pandas as pd
from lib.config import INTERMEDIATE

SCOUTING_BALLPARK = {"transitions": 4211, "admissions": 3784}
TOLERANCE = 0.30


def main():
    transitions = pd.read_parquet(INTERMEDIATE / "icu_floor_transitions.parquet")
    orders = pd.read_parquet(INTERMEDIATE / "asm_orders.parquet")

    merged = transitions.merge(orders, on="hadm_id", how="inner")
    active = merged[
        (merged["starttime"] <= merged["icu_outtime"])
        & (merged["stoptime"].isna() | (merged["stoptime"] >= merged["icu_outtime"]))
    ]

    eligible_stay_ids = active["stay_id"].unique()
    eligible_transitions = transitions[transitions["stay_id"].isin(eligible_stay_ids)].copy()
    active_orders = active[["stay_id", "pharmacy_id", "canonical_drug", "route_class",
                             "expected_interval_hours", "starttime", "stoptime"]].drop_duplicates()

    eligible_transitions.to_parquet(INTERMEDIATE / "eligible_transitions.parquet", index=False)
    active_orders.to_parquet(INTERMEDIATE / "active_asm_at_transition.parquet", index=False)

    n_transitions = len(eligible_transitions)
    n_admissions = eligible_transitions["hadm_id"].nunique()
    print(f"eligible transitions: {n_transitions}  eligible admissions: {n_admissions}")
    for label, n in (("transitions", n_transitions), ("admissions", n_admissions)):
        target = SCOUTING_BALLPARK[label]
        if abs(n - target) / target > TOLERANCE:
            print(f"WARNING: {label} count {n} is >{TOLERANCE:.0%} off the scouting-recon ballpark "
                  f"({target}) -- inspect the eligibility join before proceeding to Task 6.")


if __name__ == "__main__":
    main()
