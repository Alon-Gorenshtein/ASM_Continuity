"""Figure 1: cohort-flow diagram from epilepsy diagnosis to the analysis dataset."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

from lib.config import PROJECT_ROOT

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

LANCET_BLUE = "#00468B"
LANCET_GREY = "#ADB6B6"
LABEL_COLOR = "#2B2B2B"
MUTED_COLOR = "#6B7280"
BOX_FILL = "#EEF1F5"
BOX_BORDER = "#B5BDC8"

with open(PROJECT_ROOT / "output" / "results_digest.json") as f:
    digest = json.load(f)
cf = digest["cohort_flow"]

boxes = [
    (f"Epilepsy/status-epilepticus admissions\nMIMIC-IV v3.1, ICD-9 345.x / ICD-10 G40.x\nn = {cf['epilepsy_admissions']:,} ({cf['epilepsy_subjects']:,} patients)", None),
    (f"ICU-to-floor transitions\nn = {cf['icu_to_floor_transitions']:,}",
     "Excludes admissions without an ICU stay\nfollowed by a non-critical-care floor transfer"),
    (f"Eligible transitions\n(scheduled ASM order active at ICU departure)\nn = {cf['eligible_transitions']:,} transitions\n({cf['eligible_admissions']:,} admissions)",
     "Excludes transitions with no scheduled ASM\norder spanning ICU departure"),
    (f"Active ASM-order observations\nat eligible transitions\nn = {cf['drug_observations_before_dose_confirmation']:,} transition × drug rows",
     "One row per distinct ASM order\nactive at each eligible transition"),
    (f"Confirmed pre-transfer ICU dose\nn = {cf['analysis_dataset_rows'] + cf['not_evaluable_count']:,} transition × drug observations",
     "Excludes drug-order rows with no\nconfirmed pre-transfer ICU dose"),
    (f"Analysis dataset (evaluable)\nn = {cf['analysis_dataset_rows']:,} observations\n({cf['analysis_dataset_admissions']:,} admissions, {cf['analysis_dataset_subjects']:,} patients)",
     f"Excludes {cf['not_evaluable_count']} observations where the next\nscheduled dose was never due before discharge"),
]

fig, ax = plt.subplots(figsize=(6.6, 12.5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")

box_w, box_h = 8.0, 1.35
y_positions = [9.2, 7.52, 5.84, 4.16, 2.48, 0.8]

for (label, excl), y in zip(boxes, y_positions):
    box = FancyBboxPatch(
        (1.0, y - box_h / 2), box_w, box_h,
        boxstyle="round,pad=0.08,rounding_size=0.12",
        linewidth=1.1, edgecolor=BOX_BORDER, facecolor=BOX_FILL, zorder=2,
    )
    ax.add_patch(box)
    ax.text(5.0, y, label, ha="center", va="center", fontsize=9.5,
             color=LABEL_COLOR, zorder=3, linespacing=1.5)

for i in range(len(y_positions) - 1):
    y_top = y_positions[i] - box_h / 2
    y_bot = y_positions[i + 1] + box_h / 2
    arrow = FancyArrowPatch(
        (5.0, y_top), (5.0, y_bot),
        arrowstyle="-|>", mutation_scale=14, linewidth=1.2,
        color=LANCET_BLUE, zorder=1,
    )
    ax.add_patch(arrow)
    excl = boxes[i + 1][1]
    if excl:
        mid_y = (y_top + y_bot) / 2
        ax.text(9.3, mid_y, excl, ha="left", va="center", fontsize=8,
                 color=MUTED_COLOR, style="italic", linespacing=1.4)

out_dir = PROJECT_ROOT / "output" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
fig.savefig(out_dir / "figure1_cohort_flow.pdf", dpi=600, bbox_inches="tight", pad_inches=0.15)
fig.savefig(out_dir / "figure1_cohort_flow.png", dpi=600, bbox_inches="tight", pad_inches=0.15)
print("Wrote figure1_cohort_flow.pdf/.png")
