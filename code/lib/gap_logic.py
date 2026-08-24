"""Core measurement logic for the primary and secondary outcomes. Kept dependency-free of any real
MIMIC file so it is fully unit-testable with small fixture frames (see tests/test_gap_logic.py)."""
import pandas as pd


def compute_gaps_for_threshold(eligible, active_orders, emar_admin, dischtime_by_hadm, threshold):
    orders_by_stay = active_orders.groupby("stay_id")

    # Scope eMAR lookups to (subject_id, hadm_id) when hadm_id is available, so a dose from an
    # unrelated prior/subsequent hospitalization of the same subject is never mistaken for a dose
    # from the admission containing this ICU-to-floor transition. Falls back to subject_id-only
    # grouping when emar_admin has no hadm_id column (e.g. the fixture frames in
    # tests/test_gap_logic.py), which reproduces the original single-admission behavior exactly.
    scope_by_hadm = "hadm_id" in emar_admin.columns
    if scope_by_hadm:
        emar_by_key = {key: g.sort_values("charttime")
                       for key, g in emar_admin.groupby(["subject_id", "hadm_id"])}
    else:
        emar_by_key = {(sid,): g.sort_values("charttime")
                       for sid, g in emar_admin.groupby("subject_id")}

    rows = []
    for _, transition in eligible.iterrows():
        stay_id = transition["stay_id"]
        subject_id = transition["subject_id"]
        hadm_id = transition["hadm_id"]
        icu_outtime = transition["icu_outtime"]
        dischtime = dischtime_by_hadm.get(hadm_id)
        key = (subject_id, hadm_id) if scope_by_hadm else (subject_id,)
        subj_emar = emar_by_key.get(key)
        if subj_emar is None or stay_id not in orders_by_stay.groups:
            continue

        stay_orders = orders_by_stay.get_group(stay_id)
        for drug in stay_orders["canonical_drug"].unique():
            expected_hours = stay_orders.loc[
                stay_orders["canonical_drug"] == drug, "expected_interval_hours"
            ].iloc[0]

            drug_doses = subj_emar[subj_emar["canonical_drug"] == drug]
            before = drug_doses[drug_doses["charttime"] <= icu_outtime]
            if before.empty:
                continue  # no confirmed ICU administration to benchmark the gap from
            last_icu_dose = before["charttime"].max()

            after = drug_doses[drug_doses["charttime"] > icu_outtime]
            first_floor_dose = after["charttime"].min() if len(after) else pd.NaT

            other_drug_doses = subj_emar[subj_emar["canonical_drug"] != drug]
            window = other_drug_doses[
                (other_drug_doses["charttime"] >= icu_outtime)
                & (other_drug_doses["charttime"] <= icu_outtime + pd.Timedelta(hours=24))
            ]
            same_day_switch = len(window) > 0

            if pd.isna(first_floor_dose):
                next_due = last_icu_dose + pd.Timedelta(hours=float(expected_hours))
                if pd.notna(dischtime) and next_due >= dischtime:
                    # Discharged before the next dose was ever due -- not a gap, not evaluable.
                    evaluable = False
                    resumed = None
                    gap_hours = None
                    gap_flag = False
                else:
                    evaluable = True
                    resumed = False
                    gap_hours = ((dischtime - last_icu_dose).total_seconds() / 3600
                                 if pd.notna(dischtime) else None)
                    gap_flag = True
            else:
                evaluable = True
                resumed = True
                gap_hours = (first_floor_dose - last_icu_dose).total_seconds() / 3600
                gap_flag = bool(gap_hours > threshold * expected_hours)

            rows.append({
                "stay_id": stay_id, "subject_id": subject_id, "hadm_id": hadm_id,
                "canonical_drug": drug, "expected_interval_hours": expected_hours,
                "last_icu_dose": last_icu_dose, "first_floor_dose": first_floor_dose,
                "gap_hours": gap_hours, "gap_flag": gap_flag, "evaluable": evaluable,
                "resumed_before_discharge": resumed, "same_day_switch": same_day_switch,
                "threshold": threshold,
            })
    return pd.DataFrame(rows)
