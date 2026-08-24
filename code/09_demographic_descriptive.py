"""Descriptive-only demographic breakdown, replacing the original 51-term regression's unstable
per-category race/language/insurance/marital_status coefficients (4.5 events per variable, and
alphabetically-arbitrary reference categories such as American Indian/Alaska Native and American Sign
Language). Categories are collapsed to have a minimum usable cell size; each variable gets a single
omnibus chi-square test rather than dozens of individually unstable adjusted odds ratios. This table
is exploratory and is reported as such -- it is not the primary inferential analysis."""
import json
import pandas as pd
from scipy.stats import chi2_contingency
from lib.config import INTERMEDIATE, TABLES
from lib.stats_utils import wilson_ci

OMB_RACE_CATEGORIES = {
    "WHITE": "White", "BLACK/AFRICAN AMERICAN": "Black/African American",
    "ASIAN": "Asian", "HISPANIC/LATINO": "Hispanic/Latino",
    "AMERICAN INDIAN/ALASKA NATIVE": "Other/Unknown",
}


def collapse_race(value):
    if not isinstance(value, str):
        return "Other/Unknown"
    upper = value.upper()
    for prefix, label in OMB_RACE_CATEGORIES.items():
        if upper.startswith(prefix):
            return label
    if "WHITE" in upper:
        return "White"
    if "BLACK" in upper or "AFRICAN" in upper:
        return "Black/African American"
    if "ASIAN" in upper:
        return "Asian"
    if "HISPANIC" in upper or "LATINO" in upper:
        return "Hispanic/Latino"
    return "Other/Unknown"


def collapse_language(value):
    if not isinstance(value, str):
        return "Unknown"
    return "English" if value.strip().upper() == "ENGLISH" else "Non-English/Other"


def summarize_variable(df, col):
    categories = {}
    for cat, group in df.groupby(col):
        n_gap = int(group["gap_flag"].sum())
        n = len(group)
        lo, hi = wilson_ci(n_gap, n)
        categories[str(cat)] = {"n": n, "n_gap": n_gap, "rate": n_gap / n, "ci_low": lo, "ci_high": hi}
    table = pd.crosstab(df[col], df["gap_flag"])
    chi2, p, dof, _ = chi2_contingency(table)
    return {"categories": categories, "omnibus_chi2": float(chi2), "omnibus_p": float(p),
            "omnibus_dof": int(dof)}


def main():
    df = pd.read_parquet(INTERMEDIATE / "analysis_dataset.parquet")
    df = df.dropna(subset=["gap_flag"])
    df["race_collapsed"] = df["race"].apply(collapse_race)
    df["language_collapsed"] = df["language"].apply(collapse_language)

    out = {
        "race_collapsed": summarize_variable(df, "race_collapsed"),
        "language_collapsed": summarize_variable(df, "language_collapsed"),
        "insurance": summarize_variable(df.dropna(subset=["insurance"]), "insurance"),
        "marital_status": summarize_variable(df.dropna(subset=["marital_status"]), "marital_status"),
    }
    TABLES.mkdir(parents=True, exist_ok=True)
    with open(TABLES / "demographic_descriptive.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    for var, result in out.items():
        print(f"{var}: {len(result['categories'])} categories, omnibus p={result['omnibus_p']:.3f}")


if __name__ == "__main__":
    main()
