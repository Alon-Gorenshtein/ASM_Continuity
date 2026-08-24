"""Build ICU-to-floor transition events for epilepsy-cohort admissions.

An eligible transition is: an ICU stay (icustays.csv.gz) belonging to an epilepsy admission, whose
outtime exactly matches the intime of the NEXT transfers.csv.gz row for that admission, where that
next row is a non-ICU inpatient ward (not another ICU/CCU, not ED, not a discharge event). "Floor"
here includes step-down/intermediate units (e.g. Neuro Stepdown) -- any de-escalation out of a
critical-care-level unit counts as the transition of interest.
"""
import pandas as pd
from lib.config import MIMIC_HOSP, MIMIC_ICU, INTERMEDIATE

NON_WARD_CAREUNITS = {"UNKNOWN", "Emergency Department", "Emergency Department Observation",
                       "Discharge Lounge", "PACU"}


def is_critical_care_unit(careunit):
    return careunit.str.contains("Intensive Care", case=False, na=False) | (
        careunit == "Coronary Care Unit (CCU)"
    )


def main():
    epilepsy = pd.read_parquet(INTERMEDIATE / "epilepsy_admissions.parquet")

    icustays = pd.read_csv(
        MIMIC_ICU / "icustays.csv.gz",
        usecols=["subject_id", "hadm_id", "stay_id", "outtime"],
        dtype={"subject_id": "Int64", "hadm_id": "Int64", "stay_id": "Int64"},
        parse_dates=["outtime"],
    )
    icustays = icustays.merge(epilepsy[["hadm_id"]], on="hadm_id", how="inner")

    transfers = pd.read_csv(
        MIMIC_HOSP / "transfers.csv.gz",
        usecols=["hadm_id", "eventtype", "careunit", "intime"],
        dtype={"hadm_id": "Int64"},
        parse_dates=["intime"],
    )
    transfers = transfers.merge(epilepsy[["hadm_id"]], on="hadm_id", how="inner")

    merged = icustays.merge(transfers, left_on=["hadm_id", "outtime"], right_on=["hadm_id", "intime"])
    is_ward = (
        (~is_critical_care_unit(merged["careunit"]))
        & (~merged["careunit"].isin(NON_WARD_CAREUNITS))
        & (merged["eventtype"] != "discharge")
    )

    transitions = merged.loc[is_ward, ["stay_id", "subject_id", "hadm_id", "outtime", "careunit", "intime"]]
    transitions = transitions.rename(columns={"outtime": "icu_outtime", "intime": "floor_intime"})
    transitions = transitions.drop_duplicates(subset=["stay_id"])

    INTERMEDIATE.mkdir(parents=True, exist_ok=True)
    transitions.to_parquet(INTERMEDIATE / "icu_floor_transitions.parquet", index=False)
    print(f"ICU-to-floor transitions: {len(transitions)}  "
          f"unique admissions: {transitions['hadm_id'].nunique()}")


if __name__ == "__main__":
    main()
