"""Extract scheduled, non-alcohol-withdrawal ASM pharmacy orders for the epilepsy cohort.

pharmacy.csv.gz is 502 MB gzipped with a quoted, comma-containing disp_sched field (e.g. "08, 20"),
so naive awk -F',' column splitting silently misaligns every field after it. Fix: filter whole LINES
by a case-insensitive ASM-name regex (a text match on the raw line, no column split) with awk, keep
the header, and let pandas.read_csv do the real quote-aware column parsing on the much smaller
filtered file.
"""
import subprocess
import pandas as pd
from lib.config import MIMIC_HOSP, INTERMEDIATE
from lib.asm_vocab import (
    ASM_NAME_PATTERN, NON_SCHEDULED_PATTERN, canonical_drug, route_class,
    is_alcohol_withdrawal_order, expected_interval_hours,
)

FILTERED_CSV = INTERMEDIATE / "pharmacy_asm_filtered.csv"


def prefilter():
    src = MIMIC_HOSP / "pharmacy.csv.gz"
    pattern = ASM_NAME_PATTERN.pattern
    cmd = (
        f'gzcat "{src}" | LC_ALL=C awk -F, '
        f"'NR==1{{print; next}} tolower($0) ~ /{pattern}/' "
        f'> "{FILTERED_CSV}"'
    )
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("pharmacy prefilter failed: " + r.stderr[:500])


def main():
    INTERMEDIATE.mkdir(parents=True, exist_ok=True)
    prefilter()
    orders = pd.read_csv(FILTERED_CSV, dtype=str)

    orders["canonical_drug"] = orders["medication"].apply(canonical_drug)
    orders = orders.dropna(subset=["canonical_drug"])

    epilepsy = pd.read_parquet(INTERMEDIATE / "epilepsy_admissions.parquet")
    orders["hadm_id"] = pd.to_numeric(orders["hadm_id"], errors="coerce")
    orders = orders.merge(epilepsy[["hadm_id"]], on="hadm_id", how="inner")

    orders = orders[~orders["medication"].apply(is_alcohol_withdrawal_order)]
    orders = orders[~orders["frequency"].fillna("").apply(lambda f: bool(NON_SCHEDULED_PATTERN.search(f)))]

    orders["route_class"] = orders["canonical_drug"].apply(route_class)
    orders["expected_interval_hours"] = orders["doses_per_24_hrs"].apply(expected_interval_hours)
    orders = orders.dropna(subset=["expected_interval_hours"])

    orders["subject_id"] = pd.to_numeric(orders["subject_id"], errors="coerce").astype("int64")
    orders["hadm_id"] = orders["hadm_id"].astype("int64")
    orders["starttime"] = pd.to_datetime(orders["starttime"], errors="coerce")
    orders["stoptime"] = pd.to_datetime(orders["stoptime"], errors="coerce")
    orders = orders.dropna(subset=["starttime"])

    keep = ["subject_id", "hadm_id", "pharmacy_id", "medication", "canonical_drug", "route_class",
            "route", "frequency", "doses_per_24_hrs", "expected_interval_hours", "starttime", "stoptime"]
    orders = orders[keep].drop_duplicates()
    orders.to_parquet(INTERMEDIATE / "asm_orders.parquet", index=False)
    print(f"ASM orders (scheduled, non-alcohol-taper): {len(orders)}  "
          f"admissions: {orders['hadm_id'].nunique()}  drugs: {sorted(orders['canonical_drug'].unique())}")


if __name__ == "__main__":
    main()
