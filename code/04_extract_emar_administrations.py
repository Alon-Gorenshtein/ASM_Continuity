"""Extract eMAR dose records for ASM medications, restricted to subjects in the eligible cohort.

emar.csv.gz is 774 MB gzipped. Same whole-line regex prefilter approach as pharmacy.csv.gz (Task 4)
-- filter by matching the raw line text, not by splitting into columns, then let pandas.read_csv do
the real parsing on the smaller filtered file.
"""
import subprocess
import pandas as pd
from lib.config import MIMIC_HOSP, INTERMEDIATE
from lib.asm_vocab import ASM_NAME_PATTERN, canonical_drug

FILTERED_CSV = INTERMEDIATE / "emar_asm_filtered.csv"


def prefilter():
    src = MIMIC_HOSP / "emar.csv.gz"
    pattern = ASM_NAME_PATTERN.pattern
    cmd = (
        f'gzcat "{src}" | LC_ALL=C awk -F, '
        f"'NR==1{{print; next}} tolower($0) ~ /{pattern}/' "
        f'> "{FILTERED_CSV}"'
    )
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("emar prefilter failed: " + r.stderr[:500])


def main():
    INTERMEDIATE.mkdir(parents=True, exist_ok=True)
    prefilter()
    emar = pd.read_csv(FILTERED_CSV, dtype=str)

    emar["canonical_drug"] = emar["medication"].apply(canonical_drug)
    emar = emar.dropna(subset=["canonical_drug"])

    eligible = pd.read_parquet(INTERMEDIATE / "eligible_transitions.parquet")
    emar["subject_id"] = pd.to_numeric(emar["subject_id"], errors="coerce")
    emar = emar.merge(eligible[["subject_id"]].drop_duplicates(), on="subject_id", how="inner")

    emar["hadm_id"] = pd.to_numeric(emar["hadm_id"], errors="coerce")
    emar["charttime"] = pd.to_datetime(emar["charttime"], errors="coerce")
    emar = emar.dropna(subset=["hadm_id", "charttime"])
    emar["subject_id"] = emar["subject_id"].astype("int64")
    emar["hadm_id"] = emar["hadm_id"].astype("int64")

    keep = ["subject_id", "hadm_id", "emar_id", "canonical_drug", "event_txt", "charttime"]
    emar = emar[keep].drop_duplicates()
    emar.to_parquet(INTERMEDIATE / "asm_emar.parquet", index=False)
    print(f"ASM emar rows: {len(emar)}  administered-status rows: "
          f"{emar['event_txt'].isin(['Administered', 'Delayed Administered', 'Administered Bolus from IV Drip']).sum()}")


if __name__ == "__main__":
    main()
