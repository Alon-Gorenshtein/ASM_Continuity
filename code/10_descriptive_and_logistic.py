import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests
from lib.config import INTERMEDIATE, TABLES
from lib.stats_utils import cluster_bootstrap_dataframe

N_BOOTSTRAP = 5000
RANDOM_SEED = 20260823
PRIMARY_PREDICTORS = ["route_class", "icu_los_days", "status_epilepticus", "polytherapy_count",
                      "age", "sex"]


def cluster_bootstrap_rate_ci(df, rng):
    samples = np.empty(N_BOOTSTRAP)
    for b in range(N_BOOTSTRAP):
        resampled = cluster_bootstrap_dataframe(df, "hadm_id", rng)
        samples[b] = resampled["gap_flag"].mean()
    return float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))


def main():
    df = pd.read_parquet(INTERMEDIATE / "analysis_dataset.parquet")
    rng = np.random.default_rng(RANDOM_SEED)

    n = len(df)
    n_gap = int(df["gap_flag"].sum())
    ci_lo, ci_hi = cluster_bootstrap_rate_ci(df, np.random.default_rng(RANDOM_SEED))
    overall = {"n": n, "n_gap": n_gap, "rate": n_gap / n, "ci_low": ci_lo, "ci_high": ci_hi}

    by_drug_class = {}
    for cls, g in df.groupby("route_class"):
        ng = int(g["gap_flag"].sum())
        clo, chi = cluster_bootstrap_rate_ci(g, np.random.default_rng(RANDOM_SEED + 1))
        by_drug_class[cls] = {"n": len(g), "n_gap": ng, "rate": ng / len(g), "ci_low": clo, "ci_high": chi}

    model_df = df[["hadm_id", "gap_flag"] + PRIMARY_PREDICTORS].dropna()
    X = pd.get_dummies(model_df[PRIMARY_PREDICTORS], drop_first=True)
    y = model_df["gap_flag"].astype(int)
    Xy = pd.concat([model_df[["hadm_id"]].reset_index(drop=True),
                    X.reset_index(drop=True), y.rename("y").reset_index(drop=True)], axis=1)

    pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    pipeline.fit(X, y)
    point_or = np.exp(pipeline.named_steps["logisticregression"].coef_[0])

    boot_or = np.full((N_BOOTSTRAP, len(X.columns)), np.nan)
    for b in range(N_BOOTSTRAP):
        resampled = cluster_bootstrap_dataframe(Xy, "hadm_id", rng)
        Xb, yb = resampled[X.columns], resampled["y"]
        if yb.nunique() < 2:
            continue
        pb = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(Xb, yb)
        boot_or[b] = np.exp(pb.named_steps["logisticregression"].coef_[0])

    results, pvals = [], []
    for i, col in enumerate(X.columns):
        samples = boot_or[:, i]
        samples = samples[~np.isnan(samples) & np.isfinite(samples)]
        ci_lo_i, ci_hi_i = np.percentile(samples, [2.5, 97.5])
        p = min(1.0, 2 * min((samples <= 1).mean(), (samples >= 1).mean()))
        pvals.append(p)
        results.append({"predictor": col, "odds_ratio": float(point_or[i]),
                         "ci_low": float(ci_lo_i), "ci_high": float(ci_hi_i), "p": float(p)})

    _, p_adj, _, _ = multipletests(pvals, method="fdr_bh")
    for r, p_bh in zip(results, p_adj):
        r["p_bh"] = float(p_bh)

    TABLES.mkdir(parents=True, exist_ok=True)
    out = {"overall": overall, "by_drug_class": by_drug_class, "logistic_regression": results}
    with open(TABLES / "descriptive_and_logistic.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print(f"overall gap rate: {overall['rate']:.3f} "
          f"[{overall['ci_low']:.3f}, {overall['ci_high']:.3f}]  n={overall['n']} (cluster-bootstrap CI)")


if __name__ == "__main__":
    main()
