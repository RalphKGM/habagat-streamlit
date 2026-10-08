"""Fig. 1 of the paper: study pipeline, two rows of three steps, one column wide (3.36 in)."""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

STEPS = [
    ("NASA POWER", "Hourly weather\nJan 2020–Jun 2026"),
    ("Physical model", "1 MWdc PV, 1 MW wind\nmodeled output"),
    ("Year folds", "Fit, select, refit\ntest 2024, 2025, 2026"),
    ("Forecasts at 00:00", "Persistence, climatology\nridge, RF, XGBoost"),
    ("Battery replay", "Synthetic demand\n2 MWh grid plan"),
    ("Evidence", "MAE, paired intervals\ngrid-plan adjustment"),
]
W, H, GAP, VGAP = 1.0, 0.62, 0.17, 0.26
EDGE, FILL = "#4A5560", "#F3F4F6"

fig, ax = plt.subplots(figsize=(3.36, 1.62), dpi=400)
plt.rcParams["font.family"] = "DejaVu Sans"
for i, (head, body) in enumerate(STEPS):
    row, col = divmod(i, 3)
    x, y = col * (W + GAP), -row * (H + VGAP)
    ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle="round,pad=0,rounding_size=0.03", fc=FILL, ec=EDGE, lw=0.8))
    ax.text(x + W / 2, y + H * 0.73, head, ha="center", va="center", fontsize=6.2, fontweight="bold")
    ax.text(x + W / 2, y + H * 0.33, body, ha="center", va="center", fontsize=5.0, linespacing=1.25)
    if col < 2:
        ax.annotate("", xy=(x + W + GAP - 0.02, y + H / 2), xytext=(x + W + 0.02, y + H / 2),
                    arrowprops=dict(arrowstyle="->", color=EDGE, lw=0.8))
# elbow from step 3 down to step 4
x3, ymid = 2 * (W + GAP) + W / 2, -VGAP / 2
ax.plot([x3, x3], [0, ymid], color=EDGE, lw=0.8)
ax.plot([x3, W / 2], [ymid, ymid], color=EDGE, lw=0.8)
ax.annotate("", xy=(W / 2, -VGAP + 0.01), xytext=(W / 2, ymid), arrowprops=dict(arrowstyle="->", color=EDGE, lw=0.8))
ax.set_xlim(-0.02, 3 * W + 2 * GAP + 0.02)
ax.set_ylim(-(H + VGAP) - 0.02, H + 0.02)
ax.axis("off")
fig.subplots_adjust(0, 0, 1, 1)
fig.savefig(sys.argv[1], dpi=400)
