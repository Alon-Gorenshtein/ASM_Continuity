import pandas as pd
from lib.config import MIMIC_HOSP, MIMIC_ICU, INTERMEDIATE

PRIMARY_THRESHOLD = "1.5"


def main():
    gaps = pd.read_parquet(INTERMEDIATE / f"gaps_threshold_{PRIMARY_THRESHOLD}.parquet")
    gaps = gaps[gaps["evaluable"]].copy()
    active_orders = pd.read_parquet(INTERMEDIATE / "active_asm_at_transition.parquet")
    epilepsy = pd.read_parquet(INTERMEDIATE / "epilepsy_admissions.parquet")

    polytherapy = active_orders.groupby("stay_id")["canonical_drug"].nunique().rename("polytherapy_count")
    df = gaps.merge(polytherapy, on="stay_id", how="left")

    route_class = active_orders.drop_duplicates(subset=["stay_id", "canonical_drug"])[
        ["stay_id", "canonical_drug", "route_class"]
    ]
    df = df.merge(route_class, on=["stay_id", "canonical_drug"], how="left")
    df = df.merge(epilepsy[["hadm_id", "status_epilepticus"]], on="hadm_id", how="left")

    icustays = pd.read_csv(
        MIMIC_ICU / "icustays.csv.gz", usecols=["stay_id", "los", "first_careunit"],
        dtype={"stay_id": "int64"},
    ).rename(columns={"los": "icu_los_days", "first_careunit": "source_icu_type"})
    df = df.merge(icustays, on="stay_id", how="left")

    admissions = pd.read_csv(
        MIMIC_HOSP / "admissions.csv.gz",
        usecols=["hadm_id", "insurance", "language", "marital_status", "race"],
        dtype={"hadm_id": "int64"},
    )
    df = df.merge(admissions, on="hadm_id", how="left")

    patients = pd.read_csv(
        MIMIC_HOSP / "patients.csv.gz", usecols=["subject_id", "gender", "anchor_age"],
        dtype={"subject_id": "int64"},
    ).rename(columns={"gender": "sex", "anchor_age": "age"})
    df = df.merge(patients, on="subject_id", how="left")

    transitions = pd.read_parquet(INTERMEDIATE / "icu_floor_transitions.parquet")[
        ["stay_id", "icu_outtime", "careunit"]
    ].rename(columns={"careunit": "destination_careunit"})
    df = df.merge(transitions, on="stay_id", how="left")
    df["transfer_hour"] = df["icu_outtime"].dt.hour
    df["transfer_is_weekend"] = df["icu_outtime"].dt.dayofweek >= 5
    df["destination_ward_type"] = df["destination_careunit"].str.contains(
        "Intermediate|Stepdown|Step-Down", case=False, na=False
    ).map({True: "stepdown", False: "regular_floor"})
    df = df.drop(columns=["destination_careunit"])

    df.to_parquet(INTERMEDIATE / "analysis_dataset.parquet", index=False)
    print(f"analysis dataset rows: {len(df)}  admissions: {df['hadm_id'].nunique()}  "
          f"gap rate: {df['gap_flag'].mean():.3f}")


if __name__ == "__main__":
    main()
