import pandas as pd
from lib.config import MIMIC_HOSP, INTERMEDIATE
from lib.gap_logic import compute_gaps_for_threshold

THRESHOLDS = (1.5, 2.0, 3.0)


def main():
    eligible = pd.read_parquet(INTERMEDIATE / "eligible_transitions.parquet")
    active_orders = pd.read_parquet(INTERMEDIATE / "active_asm_at_transition.parquet")
    emar = pd.read_parquet(INTERMEDIATE / "asm_emar.parquet")
    emar = emar[emar["event_txt"].isin(
        ["Administered", "Delayed Administered", "Administered Bolus from IV Drip"]
    )]

    admissions = pd.read_csv(
        MIMIC_HOSP / "admissions.csv.gz", usecols=["hadm_id", "dischtime"],
        dtype={"hadm_id": "int64"}, parse_dates=["dischtime"],
    )
    dischtime_by_hadm = admissions.set_index("hadm_id")["dischtime"].to_dict()

    for threshold in THRESHOLDS:
        gaps = compute_gaps_for_threshold(eligible, active_orders, emar, dischtime_by_hadm, threshold)
        gaps.to_parquet(INTERMEDIATE / f"gaps_threshold_{threshold}.parquet", index=False)
        rate = gaps["gap_flag"].mean() if len(gaps) else float("nan")
        switches = int(gaps["same_day_switch"].sum())
        print(f"threshold {threshold}x: rows={len(gaps)}  gap_rate={rate:.3f}  same_day_switches={switches}")


if __name__ == "__main__":
    main()
