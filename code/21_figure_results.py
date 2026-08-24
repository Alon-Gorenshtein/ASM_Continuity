"""Figure 2: transfer vs. matched non-transfer control gap rates, pre- and
post-transfer (panel a); per-drug gap rates with 95% CIs, sorted low to high
(panel b); and the distribution of gap duration for resumed vs. never-resumed
administrations before discharge (panel c)."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

from lib.config import PROJECT_ROOT

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

LANCET_BLUE = "#00468B"
LANCET_GREY = "#ADB6B6"
LANCET_SALMON = "#FDAF91"
LABEL_COLOR = "#2B2B2B"
MUTED_COLOR = "#6B7280"

with open(PROJECT_ROOT / "output" / "stats_digest.json") as f:
    stats = json.load(f)
tvc = stats["transfer_vs_control"]
by_drug = stats["iv_oral_and_sensitivity"]["by_drug"]
delay = stats["delay_duration"]

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15.5, 5.2), gridspec_kw={"width_ratios": [1, 1.3, 1]})

# --- Panel a: transfer vs. matched non-transfer control (paired comparison) ---
panels = [
    ("Pre-transfer\ncontrol", tvc["pre_control"]),
    ("Post-transfer\ncontrol", tvc["post_control"]),
]
x = np.arange(len(panels))
width = 0.32
transfer_rates = [p["transfer_gap_rate"] * 100 for _, p in panels]
control_rates = [p["control_gap_rate"] * 100 for _, p in panels]
ax1.bar(x - width / 2, transfer_rates, width, color=LANCET_SALMON, label="Transfer-crossing interval")
ax1.bar(x + width / 2, control_rates, width, color=LANCET_BLUE, label="Matched non-transfer interval")
for xi, (_, p) in zip(x, panels):
    ax1.text(xi, max(p["transfer_gap_rate"], p["control_gap_rate"]) * 100 + 1.2,
              f"P = {p['mcnemar_p']:.1e}", ha="center", fontsize=8, color=MUTED_COLOR)
ax1.set_xticks(x)
ax1.set_xticklabels([label for label, _ in panels], fontsize=9.5, color=LABEL_COLOR)
ax1.set_ylabel("Administration gap rate, %", fontsize=10, color=LABEL_COLOR)
ax1.set_ylim(0, 12)
ax1.legend(fontsize=7.5, frameon=False, loc="upper left")
ax1.tick_params(axis="both", colors=MUTED_COLOR, labelsize=9)
for spine in ("bottom", "left"):
    ax1.spines[spine].set_color("#9CA3AF")
ax1.grid(axis="y", color="#F3F4F6", lw=0.6, zorder=0)
ax1.text(-0.16, 1.05, "a", transform=ax1.transAxes, fontsize=14, fontweight="bold", color=LABEL_COLOR)

# --- Panel b: per-drug gap rates ---
drug_order = sorted(by_drug.items(), key=lambda kv: kv[1]["rate"])
yb = np.arange(len(drug_order))
for yi, (drug, d) in zip(yb, drug_order):
    rate, lo, hi = d["rate"] * 100, d["ci_low"] * 100, d["ci_high"] * 100
    ax2.plot([lo, hi], [yi, yi], color=LANCET_BLUE, lw=1.6, zorder=1)
    ax2.scatter([rate], [yi], s=45, color=LANCET_BLUE, edgecolors="white", linewidths=0.8, zorder=2)
ax2.set_yticks(yb)
ax2.set_yticklabels(
    [f"{drug.capitalize()} (n={d['n']:,})" for drug, d in drug_order],
    fontsize=8.5, color=LABEL_COLOR,
)
ax2.axvline(10.2, color="#9CA3AF", lw=0.8, linestyle="--", zorder=0)
ax2.set_xlabel("Administration gap rate, % (95% CI)", fontsize=10, color=LABEL_COLOR)
ax2.set_xlim(0, 35)
ax2.tick_params(axis="both", colors=MUTED_COLOR, labelsize=9)
for spine in ("bottom", "left"):
    ax2.spines[spine].set_color("#9CA3AF")
ax2.grid(axis="x", color="#F3F4F6", lw=0.6, zorder=0)
ax2.text(-0.22, 1.05, "b", transform=ax2.transAxes, fontsize=14, fontweight="bold", color=LABEL_COLOR)

# --- Panel c: delay-duration distribution (resumed vs. never-resumed) ---
excess = delay["excess_beyond_expected"]
groups = [
    ("Resumed,\ndelayed", excess["resumed_before_discharge"]),
    ("Not resumed\nbefore discharge", excess["not_resumed_before_discharge"]),
]
yc = np.arange(len(groups))[::-1]
for yi, (label, d) in zip(yc, groups):
    ax3.plot([d["iqr_low"], d["iqr_high"]], [yi, yi], color=LANCET_BLUE, lw=5, zorder=1, alpha=0.35)
    ax3.plot([d["median"], d["median"]], [yi - 0.18, yi + 0.18], color=LANCET_BLUE, lw=2.2, zorder=2)
    ax3.scatter([d["p90"]], [yi], s=40, color=LANCET_SALMON, marker="D", zorder=3)
    ax3.text(max(d["iqr_high"], d["p90"]) + 8, yi, f"median {d['median']:.0f}h (n={d['n']})",
              va="center", fontsize=8, color=MUTED_COLOR)
ax3.set_yticks(yc)
ax3.set_yticklabels([g[0] for g in groups], fontsize=9.5, color=LABEL_COLOR)
ax3.set_xlabel("Excess beyond expected dosing interval, hours\n(median, IQR bar, 90th %ile)", fontsize=9.5, color=LABEL_COLOR)
ax3.set_xlim(0, 300)
ax3.set_ylim(-0.7, len(groups) - 0.3)
ax3.tick_params(axis="both", colors=MUTED_COLOR, labelsize=9)
for spine in ("bottom", "left"):
    ax3.spines[spine].set_color("#9CA3AF")
ax3.grid(axis="x", color="#F3F4F6", lw=0.6, zorder=0)
ax3.text(-0.16, 1.05, "c", transform=ax3.transAxes, fontsize=14, fontweight="bold", color=LABEL_COLOR)

fig.subplots_adjust(wspace=0.7)

out_dir = PROJECT_ROOT / "output" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "figure2_results.pdf", dpi=600, bbox_inches="tight", pad_inches=0.15)
fig.savefig(out_dir / "figure2_results.png", dpi=600, bbox_inches="tight", pad_inches=0.15)
print("Wrote figure2_results.pdf/.png")
