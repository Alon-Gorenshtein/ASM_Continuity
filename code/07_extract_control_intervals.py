"""Build non-transfer control intervals for the McNemar comparator (Task 8/08_...).

For each evaluable transfer transition-by-drug observation, find:
  - the PRE-transfer control: the interval between the second-to-last and last ICU-charted dose of
    the same drug, both entirely within the ICU (before icu_outtime) -- a same-unit, non-transfer
    interval immediately preceding the transfer.
  - the POST-transfer control: the interval between the first and second floor-charted dose, both
    entirely on the floor (after icu_outtime) -- a same-unit, non-transfer interval immediately
    following the transfer.
Both are flagged as a gap using the identical threshold rule as the primary (transfer) interval, so
the comparison is apples-to-apples. Missing on either side (e.g. the transfer dose was the very first
ICU dose ever charted for that drug) is reported as null, not silently dropped -- see the counts test.
"""
import pandas as pd
from lib.config import INTERMEDIATE

THRESHOLDS = (1.5, 2.0, 3.0)
ADMINISTERED = {"Administered", "Delayed Administered", "Administered Bolus from IV Drip"}


def main():
    eligible = pd.read_parquet(INTERMEDIATE / "eligible_transitions.parquet")
    active_orders = pd.read_parquet(INTERMEDIATE / "active_asm_at_transition.parquet")
    emar = pd.read_parquet(INTERMEDIATE / "asm_emar.parquet")
    emar = emar[emar["event_txt"].isin(ADMINISTERED)]
    orders = pd.read_parquet(INTERMEDIATE / "asm_orders.parquet")

    orders_by_stay = active_orders.groupby("stay_id")
    orders_by_hadm_drug = orders.groupby(["hadm_id", "canonical_drug"])
    emar_by_key = {key: g.sort_values("charttime") for key, g in emar.groupby(["subject_id", "hadm_id"])}
    eligible_by_stay = eligible.set_index("stay_id")

    for t in THRESHOLDS:
        gaps = pd.read_parquet(INTERMEDIATE / f"gaps_threshold_{t}.parquet")
        gaps = gaps[gaps["evaluable"]]

        rows = []
        for _, gap_row in gaps.iterrows():
            stay_id, drug = gap_row["stay_id"], gap_row["canonical_drug"]
            transition = eligible_by_stay.loc[stay_id]
            subject_id, hadm_id, icu_outtime = (
                transition["subject_id"], transition["hadm_id"], transition["icu_outtime"]
            )
            subj_emar = emar_by_key.get((subject_id, hadm_id))
            if subj_emar is None or stay_id not in orders_by_stay.groups:
                continue
            expected_hours = float(orders_by_stay.get_group(stay_id).loc[
                orders_by_stay.get_group(stay_id)["canonical_drug"] == drug, "expected_interval_hours"
            ].iloc[0])
            drug_doses = subj_emar[subj_emar["canonical_drug"] == drug]
            before = drug_doses[drug_doses["charttime"] <= icu_outtime]
            after = drug_doses[drug_doses["charttime"] > icu_outtime]
            last_icu_dose = before["charttime"].max()
            first_floor_dose = after["charttime"].min() if len(after) else pd.NaT

            pre_gap = None
            pre_candidates = before[before["charttime"] < last_icu_dose]
            if len(pre_candidates):
                prev_dose = pre_candidates["charttime"].max()
                pre_hours = (last_icu_dose - prev_dose).total_seconds() / 3600
                pre_gap = bool(pre_hours > t * expected_hours)

            post_gap = None
            post_schedule_changed = None
            if pd.notna(first_floor_dose):
                post_candidates = after[after["charttime"] > first_floor_dose]
                if len(post_candidates):
                    next_dose = post_candidates["charttime"].min()
                    post_hours = (next_dose - first_floor_dose).total_seconds() / 3600
                    post_gap = bool(post_hours > t * expected_hours)
                    if post_gap is not None and (hadm_id, drug) in orders_by_hadm_drug.groups:
                        hadm_orders = orders_by_hadm_drug.get_group((hadm_id, drug))
                        covering = hadm_orders[
                            (hadm_orders["starttime"] <= next_dose) & (hadm_orders["stoptime"] >= first_floor_dose)
                        ]
                        if len(covering):
                            floor_expected = float(covering["expected_interval_hours"].iloc[0])
                            post_schedule_changed = abs(floor_expected - expected_hours) > 0.01

            rows.append({
                "stay_id": stay_id, "canonical_drug": drug,
                "hadm_id": hadm_id, "subject_id": subject_id,
                "transfer_gap_flag": bool(gap_row["gap_flag"]),
                "pre_gap_flag": pre_gap, "post_gap_flag": post_gap,
                "post_schedule_changed": post_schedule_changed,
            })

        out = pd.DataFrame(rows)
        out_path = (INTERMEDIATE / "control_intervals.parquet" if t == 1.5
                    else INTERMEDIATE / f"control_intervals_threshold_{t}.parquet")
        out.to_parquet(out_path, index=False)
        print(f"[{t}x] control-interval rows: {len(out)}  "
              f"has pre-control: {out['pre_gap_flag'].notna().sum()}  "
              f"has post-control: {out['post_gap_flag'].notna().sum()}  "
              f"has either: {(out['pre_gap_flag'].notna() | out['post_gap_flag'].notna()).sum()}  "
              f"schedule-checked: {out['post_schedule_changed'].notna().sum()}  "
              f"schedule-changed: {int((out['post_schedule_changed'] == True).sum())}")


if __name__ == "__main__":
    main()
