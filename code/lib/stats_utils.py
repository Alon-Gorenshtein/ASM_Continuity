"""Shared statistical helpers used across the descriptive, regression, and sensitivity scripts."""
import numpy as np


def wilson_ci(successes, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * ((p * (1 - p) / n + z**2 / (4 * n**2)) ** 0.5)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def cluster_bootstrap_dataframe(df, cluster_col, rng):
    idx_by_cluster = df.groupby(cluster_col).indices
    cluster_ids = np.array(list(idx_by_cluster.keys()))
    sampled = rng.choice(cluster_ids, size=len(cluster_ids), replace=True)
    positions = np.concatenate([idx_by_cluster[c] for c in sampled])
    return df.iloc[positions]
