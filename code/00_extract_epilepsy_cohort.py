"""Extract the epilepsy-diagnosis cohort and status-epilepticus flag from MIMIC-IV diagnoses_icd.

Epilepsy = ICD-9 345.x ("epilepsy and recurrent seizures" family) or ICD-10 G40.x. Status
epilepticus is NOT a separate ICD-10-CM category in this vocabulary (no standalone G41) -- it is a
suffix on specific G40.x codes, so those codes are identified by their long_title in
d_icd_diagnoses.csv.gz rather than guessed from the code string.
"""
import pandas as pd
from lib.config import MIMIC_HOSP, INTERMEDIATE


def load_status_epilepticus_icd10_codes():
    dx_dict = pd.read_csv(MIMIC_HOSP / "d_icd_diagnoses.csv.gz", dtype=str)
    mask = (dx_dict["icd_version"] == "10") & dx_dict["long_title"].str.contains(
        "with status epilepticus", case=False, na=False
    )
    return set(dx_dict.loc[mask, "icd_code"])


def main():
    diagnoses = pd.read_csv(
        MIMIC_HOSP / "diagnoses_icd.csv.gz",
        dtype={"subject_id": "int64", "hadm_id": "int64", "icd_code": str, "icd_version": str},
        usecols=["subject_id", "hadm_id", "icd_code", "icd_version"],
    )
    status_epi_icd10 = load_status_epilepticus_icd10_codes()

    is_epilepsy9 = (diagnoses["icd_version"] == "9") & diagnoses["icd_code"].str.startswith("345")
    is_epilepsy10 = (diagnoses["icd_version"] == "10") & diagnoses["icd_code"].str.startswith("G40")
    epilepsy = diagnoses[is_epilepsy9 | is_epilepsy10].copy()

    is_status9 = (epilepsy["icd_version"] == "9") & (epilepsy["icd_code"] == "3453")
    is_status10 = (epilepsy["icd_version"] == "10") & epilepsy["icd_code"].isin(status_epi_icd10)
    epilepsy["is_status_epilepticus_code"] = is_status9 | is_status10

    admissions = (
        epilepsy.groupby("hadm_id")
        .agg(subject_id=("subject_id", "first"),
             status_epilepticus=("is_status_epilepticus_code", "any"))
        .reset_index()
    )

    INTERMEDIATE.mkdir(parents=True, exist_ok=True)
    admissions.to_parquet(INTERMEDIATE / "epilepsy_admissions.parquet", index=False)
    print(f"epilepsy admissions: {len(admissions)}  "
          f"unique subjects: {admissions['subject_id'].nunique()}  "
          f"status-epilepticus admissions: {int(admissions['status_epilepticus'].sum())}")


if __name__ == "__main__":
    main()
