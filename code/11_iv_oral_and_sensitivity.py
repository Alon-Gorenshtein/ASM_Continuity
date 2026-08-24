import json
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from lib.config import INTERMEDIATE, TABLES
from lib.stats_utils import wilson_ci, cluster_bootstrap_dataframe

RATE_DIFF_SEED = 20260824  # distinct from 10_descriptive_and_logistic.py's 20260823 (and its +1
                            # offset for by_drug_class) to avoid identical bootstrap draw sequences
                            # across files, per the prior revision's Task 7 review note.
N_RATE_DIFF_BOOT = 5000


def cramers_v(table):
    chi2, p, dof, _ = chi2_contingency(table)
    n = table.values.sum()
    k = min(table.shape) - 1
    return chi2, p, float(np.sqrt(chi2 / (n * k))) if k > 0 else 0.0


def cluster_bootstrap_rate_diff(df, rng, n_boot=N_RATE_DIFF_BOOT):
    samples = np.empty(n_boot)
    for b in range(n_boot):
        resampled = cluster_bootstrap_dataframe(df, "hadm_id", rng)
        grouped = resampled.groupby("route_class")["gap_flag"].mean()
        oral = grouped.get("oral_only", np.nan)
        iv = grouped.get("iv_available", np.nan)
        samples[b] = oral - iv
    samples = samples[~np.isnan(samples) & np.isfinite(samples)]
    lo, hi = np.percentile(samples, [2.5, 97.5])
    p = min(1.0, 2 * min((samples <= 0).mean(), (samples >= 0).mean()))
    return float(lo), float(hi), float(p)


def main():
    df = pd.read_parquet(INTERMEDIATE / "analysis_dataset.parquet")

    table = pd.crosstab(df["route_class"], df["gap_flag"])
    chi2, p, v = cramers_v(table)
    # naive, unadjusted comparison (ignores admission-level clustering)
    iv_vs_oral = {"chi2": float(chi2), "p": float(p), "cramers_v": v,
                  "contingency_table": table.to_dict()}

    # naive chi2/cramers_v above are unadjusted for admission-level clustering
    # (patients contribute multiple ASM/transition rows); the fields below are
    # the properly admission-cluster-adjusted comparison.
    rng = np.random.default_rng(RATE_DIFF_SEED)
    rate_diff = float(
        df[df["route_class"] == "oral_only"]["gap_flag"].mean()
        - df[df["route_class"] == "iv_available"]["gap_flag"].mean()
    )
    rd_lo, rd_hi, rd_p = cluster_bootstrap_rate_diff(df, rng)
    iv_vs_oral["rate_diff"] = rate_diff
    iv_vs_oral["rate_diff_ci_low"] = rd_lo
    iv_vs_oral["rate_diff_ci_high"] = rd_hi
    iv_vs_oral["rate_diff_bootstrap_p"] = rd_p

    threshold_sensitivity = []
    for t in ("1.5", "2.0", "3.0"):
        g = pd.read_parquet(INTERMEDIATE / f"gaps_threshold_{t}.parquet")
        g = g[g["evaluable"]]
        n_gap = int(g["gap_flag"].sum())
        lo, hi = wilson_ci(n_gap, len(g))
        threshold_sensitivity.append({
            "threshold": float(t), "n": len(g), "gap_rate": float(g["gap_flag"].mean()),
            "ci_low": lo, "ci_high": hi,
        })

    one_per_admission = df.sort_values("stay_id").drop_duplicates(subset=["hadm_id"], keep="first")
    n_gap = int(one_per_admission["gap_flag"].sum())
    lo, hi = wilson_ci(n_gap, len(one_per_admission))
    clustering_sensitivity = {"n": len(one_per_admission), "n_gap": n_gap,
                               "gap_rate": n_gap / len(one_per_admission), "ci_low": lo, "ci_high": hi}

    switch_excluded = df[~df["same_day_switch"]]
    n_excluded = int(df["same_day_switch"].sum())
    n_gap_sw = int(switch_excluded["gap_flag"].sum())
    lo_sw, hi_sw = wilson_ci(n_gap_sw, len(switch_excluded))
    switch_excluded_sensitivity = {
        "n_excluded": n_excluded, "n_remaining": len(switch_excluded),
        "gap_rate": n_gap_sw / len(switch_excluded), "ci_low": lo_sw, "ci_high": hi_sw,
    }

    by_drug = {}
    for drug, g in df.groupby("canonical_drug"):
        ng = int(g["gap_flag"].sum())
        lo_d, hi_d = wilson_ci(ng, len(g))
        by_drug[drug] = {"n": len(g), "n_gap": ng, "rate": ng / len(g), "ci_low": lo_d, "ci_high": hi_d}

    TABLES.mkdir(parents=True, exist_ok=True)
    out = {"iv_vs_oral": iv_vs_oral, "threshold_sensitivity": threshold_sensitivity,
           "clustering_sensitivity": clustering_sensitivity,
           "switch_excluded_sensitivity": switch_excluded_sensitivity, "by_drug": by_drug}
    with open(TABLES / "iv_oral_and_sensitivity.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"IV vs oral Cramer's V: {v:.3f} (naive p={p:.4f})  "
          f"cluster-adjusted rate diff: {rate_diff:+.3f} "
          f"[{rd_lo:+.3f}, {rd_hi:+.3f}] (bootstrap p={rd_p:.3f})  "
          f"switch-excluded gap rate: {switch_excluded_sensitivity['gap_rate']:.3f} "
          f"(n_excluded={n_excluded})")


if __name__ == "__main__":
    main()
