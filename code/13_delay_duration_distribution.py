"""Distribution of the delay/gap duration itself (gap_hours), not just the binary
gap/no-gap flag -- addresses the review's request for median delay, IQR, 90th
percentile, and max, split by whether the medication was ever resumed before
discharge (a resumed-but-delayed gap and a never-resumed-before-discharge gap are
different failure modes and are not pooled into one distribution without saying so),
and by dosing-interval class (q6h/q8h/q12h/q24h), addressing the review's separate
request for a per-dosing-frequency breakdown rather than only per-drug."""
import json
import pandas as pd
from lib.config import INTERMEDIATE, TABLES
from lib.stats_utils import wilson_ci


def describe_hours(s):
    return {
        "n": int(len(s)),
        "median": float(s.median()),
        "iqr_low": float(s.quantile(0.25)),
        "iqr_high": float(s.quantile(0.75)),
        "p90": float(s.quantile(0.90)),
        "max": float(s.max()),
    }


def main():
    df = pd.read_parquet(INTERMEDIATE / "analysis_dataset.parquet")
    gaps = df[df["gap_flag"]]
    resumed = gaps[gaps["resumed_before_discharge"] == True]
    not_resumed = gaps[gaps["resumed_before_discharge"] == False]

    gaps = gaps.copy()
    gaps["excess_hours"] = gaps["gap_hours"] - gaps["expected_interval_hours"]
    resumed_excess = gaps[gaps["resumed_before_discharge"] == True]["excess_hours"]
    not_resumed_excess = gaps[gaps["resumed_before_discharge"] == False]["excess_hours"]

    by_dosing_interval = {}
    for hours, g in df.groupby("expected_interval_hours"):
        n_gap = int(g["gap_flag"].sum())
        n = len(g)
        lo, hi = wilson_ci(n_gap, n)
        by_dosing_interval[str(hours)] = {
            "n": n, "n_gap": n_gap, "rate": n_gap / n, "ci_low": lo, "ci_high": hi,
        }

    out = {
        "all_gaps": describe_hours(gaps["gap_hours"]),
        "resumed_before_discharge": describe_hours(resumed["gap_hours"]),
        "not_resumed_before_discharge": describe_hours(not_resumed["gap_hours"]),
        "excess_beyond_expected": {
            "all_gaps": describe_hours(gaps["excess_hours"]),
            "resumed_before_discharge": describe_hours(resumed_excess),
            "not_resumed_before_discharge": describe_hours(not_resumed_excess),
        },
        "by_dosing_interval": by_dosing_interval,
    }

    TABLES.mkdir(parents=True, exist_ok=True)
    with open(TABLES / "delay_duration.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

    ag = out["all_gaps"]
    print(f"delay duration (all {ag['n']} gaps): median {ag['median']:.1f}h "
          f"[IQR {ag['iqr_low']:.1f}-{ag['iqr_high']:.1f}], 90th pct {ag['p90']:.1f}h, "
          f"max {ag['max']:.1f}h")
    ex = out["excess_beyond_expected"]["all_gaps"]
    print(f"excess beyond expected interval (all {ex['n']} gaps): median {ex['median']:.1f}h "
          f"[IQR {ex['iqr_low']:.1f}-{ex['iqr_high']:.1f}], 90th pct {ex['p90']:.1f}h, max {ex['max']:.1f}h")
    for hours, d in sorted(by_dosing_interval.items(), key=lambda kv: float(kv[0])):
        print(f"  q{hours}h: n={d['n']} gap_rate={d['rate']:.3f} "
              f"[{d['ci_low']:.3f}, {d['ci_high']:.3f}]")


if __name__ == "__main__":
    main()
