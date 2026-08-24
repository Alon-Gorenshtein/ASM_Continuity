"""The primary comparator analysis: is a transfer-crossing ASM administration interval more often
flagged as a gap than a matched non-transfer interval for the SAME patient and drug? Paired exact
McNemar's test (binomial test on the discordant pairs) -- the correct test for a paired binary
outcome measured twice on the same unit (here, the same stay_id+drug, transfer vs. control).

The paired rate difference additionally gets an admission-cluster and a patient-cluster bootstrap
95% CI (5,000 resamples each), since McNemar's test alone treats matched pairs as independent, which
undercounts the true variance when one admission or one patient contributes more than one pair."""
import json
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from lib.config import INTERMEDIATE, TABLES
from lib.stats_utils import cluster_bootstrap_dataframe, wilson_ci

RATE_DIFF_SEED = 20260825
N_RATE_DIFF_BOOT = 5000


def paired_comparison(df, control_col):
    sub = df[df[control_col].notna()].copy()
    n = len(sub)
    control_flag = sub[control_col].astype(bool)
    transfer_rate = float(sub["transfer_gap_flag"].mean())
    control_rate = float(control_flag.mean())
    transfer_only = int((sub["transfer_gap_flag"] & ~control_flag).sum())
    control_only = int((~sub["transfer_gap_flag"] & control_flag).sum())
    both = int((sub["transfer_gap_flag"] & control_flag).sum())
    neither = int((~sub["transfer_gap_flag"] & ~control_flag).sum())
    total_discordant = transfer_only + control_only
    p = float(binomtest(transfer_only, total_discordant, 0.5).pvalue) if total_discordant > 0 else 1.0
    return {
        "n": n, "transfer_gap_rate": transfer_rate, "control_gap_rate": control_rate,
        "discordant_transfer_only": transfer_only, "discordant_control_only": control_only,
        "concordant_both": both, "concordant_neither": neither, "mcnemar_p": p,
    }


def cluster_rate_diff_ci(sub, control_col, cluster_col, rng, n_boot=N_RATE_DIFF_BOOT):
    diffs = []
    for _ in range(n_boot):
        boot = cluster_bootstrap_dataframe(sub, cluster_col, rng)
        control_flag = boot[control_col].astype(bool)
        diffs.append(float(boot["transfer_gap_flag"].mean() - control_flag.mean()))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(lo), float(hi)


def rate_diff_result(df, control_col):
    result = paired_comparison(df, control_col)
    sub = df[df[control_col].notna()].copy()
    result["rate_diff"] = result["transfer_gap_rate"] - result["control_gap_rate"]
    rng_h = np.random.default_rng(RATE_DIFF_SEED)
    lo_h, hi_h = cluster_rate_diff_ci(sub, control_col, "hadm_id", rng_h)
    result["rate_diff_ci_hadm"] = [lo_h, hi_h]
    rng_s = np.random.default_rng(RATE_DIFF_SEED)
    lo_s, hi_s = cluster_rate_diff_ci(sub, control_col, "subject_id", rng_s)
    result["rate_diff_ci_subject"] = [lo_s, hi_s]
    return result


def threshold_sensitivity(thresholds=(2.0, 3.0)):
    out = {}
    for t in thresholds:
        df_t = pd.read_parquet(INTERMEDIATE / f"control_intervals_threshold_{t}.parquet")
        out[str(t)] = {
            "pre_control": rate_diff_result(df_t, "pre_gap_flag"),
            "post_control": rate_diff_result(df_t, "post_gap_flag"),
        }
    return out


def selection_subset_stats(analysis, control_flag_notna_mask):
    has = analysis[control_flag_notna_mask]
    hasnt = analysis[~control_flag_notna_mask]
    out = {}
    for label, sub in (("has_control", has), ("no_control", hasnt)):
        n = len(sub)
        n_gap = int(sub["gap_flag"].sum())
        lo, hi = wilson_ci(n_gap, n)
        out[label] = {"n": n, "n_gap": n_gap, "rate": n_gap / n, "ci_low": lo, "ci_high": hi}
    return out


def main():
    df = pd.read_parquet(INTERMEDIATE / "control_intervals.parquet")
    analysis = pd.read_parquet(INTERMEDIATE / "analysis_dataset.parquet")
    merged = analysis.merge(
        df[["stay_id", "canonical_drug", "pre_gap_flag", "post_gap_flag"]],
        on=["stay_id", "canonical_drug"], how="left",
    )

    out = {
        "pre_control": rate_diff_result(df, "pre_gap_flag"),
        "post_control": rate_diff_result(df, "post_gap_flag"),
        "selection_check": {
            "pre": selection_subset_stats(merged, merged["pre_gap_flag"].notna()),
            "post": selection_subset_stats(merged, merged["post_gap_flag"].notna()),
        },
    }

    unchanged = df[df["post_schedule_changed"] == False]
    out["post_control_schedule_unchanged"] = paired_comparison(unchanged, "post_gap_flag")
    out["post_control_schedule_unchanged"]["n_checked"] = int(df["post_schedule_changed"].notna().sum())
    out["post_control_schedule_unchanged"]["n_changed"] = int((df["post_schedule_changed"] == True).sum())

    out["threshold_sensitivity"] = threshold_sensitivity()

    TABLES.mkdir(parents=True, exist_ok=True)
    with open(TABLES / "transfer_vs_control.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

    for label in ("pre_control", "post_control"):
        r = out[label]
        print(f"{label}: n={r['n']}  transfer={r['transfer_gap_rate']:.3f}  control={r['control_gap_rate']:.3f}  "
              f"p={r['mcnemar_p']:.2e}  rate_diff={r['rate_diff']:.4f} "
              f"[hadm {r['rate_diff_ci_hadm'][0]:.4f},{r['rate_diff_ci_hadm'][1]:.4f}] "
              f"[subj {r['rate_diff_ci_subject'][0]:.4f},{r['rate_diff_ci_subject'][1]:.4f}]")
    su = out["post_control_schedule_unchanged"]
    print(f"post-control, schedule-unchanged only: n={su['n']}  transfer={su['transfer_gap_rate']:.3f}  "
          f"control={su['control_gap_rate']:.3f}  p={su['mcnemar_p']:.2e}  "
          f"(checked={su['n_checked']}, changed={su['n_changed']})")

    for t_str, t_out in out["threshold_sensitivity"].items():
        for label in ("pre_control", "post_control"):
            r = t_out[label]
            print(f"[{t_str}x] {label}: n={r['n']}  transfer={r['transfer_gap_rate']:.3f}  control={r['control_gap_rate']:.3f}  "
                  f"p={r['mcnemar_p']:.2e}  rate_diff={r['rate_diff']:.4f} "
                  f"[hadm {r['rate_diff_ci_hadm'][0]:.4f},{r['rate_diff_ci_hadm'][1]:.4f}] "
                  f"[subj {r['rate_diff_ci_subject'][0]:.4f},{r['rate_diff_ci_subject'][1]:.4f}]")


if __name__ == "__main__":
    main()
