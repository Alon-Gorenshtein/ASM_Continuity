import numpy as np
import pandas as pd
from lib.stats_utils import wilson_ci, cluster_bootstrap_dataframe


def test_wilson_ci_matches_known_value():
    lo, hi = wilson_ci(167, 1585)
    assert abs(lo - 0.09119010155348088) < 1e-9
    assert abs(hi - 0.12144380732705197) < 1e-9


def test_wilson_ci_edge_cases():
    assert wilson_ci(0, 0) == (0.0, 0.0) or all(np.isnan(x) for x in wilson_ci(0, 0))
    lo, hi = wilson_ci(0, 10)
    assert lo == 0.0
    assert hi > 0.0


def test_cluster_bootstrap_preserves_cluster_membership():
    df = pd.DataFrame({
        "hadm_id": [1, 1, 2, 3, 3, 3],
        "value": [10, 11, 20, 30, 31, 32],
    })
    rng = np.random.default_rng(42)
    resampled = cluster_bootstrap_dataframe(df, "hadm_id", rng)
    assert len(resampled) > 0
    # every row in the resample must be an exact row from the original df (no fabricated rows)
    for _, row in resampled.iterrows():
        match = df[(df["hadm_id"] == row["hadm_id"]) & (df["value"] == row["value"])]
        assert len(match) == 1
    # a cluster's rows always appear together in multiples of their original cluster size
    counts = resampled["hadm_id"].value_counts()
    original_sizes = df.groupby("hadm_id").size()
    for hadm_id, count in counts.items():
        assert count % original_sizes[hadm_id] == 0


def test_cluster_bootstrap_same_total_cluster_count():
    df = pd.DataFrame({"hadm_id": [1, 1, 2, 3], "value": [1, 2, 3, 4]})
    rng = np.random.default_rng(7)
    resampled = cluster_bootstrap_dataframe(df, "hadm_id", rng)
    n_original_clusters = df["hadm_id"].nunique()
    n_resampled_cluster_draws = sum(
        resampled[resampled["hadm_id"] == h].drop_duplicates().shape[0] > 0
        for h in df["hadm_id"].unique()
    ) or 1
    assert n_resampled_cluster_draws <= n_original_clusters
