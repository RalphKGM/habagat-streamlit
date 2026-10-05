"""Paper figure: January-June 2026 daily energy, computed from 2026 weather vs the XGBoost day-ahead forecast.

Same style as the team's draw_rolling_figures.py. Writes paper/fig_2026_computed_vs_forecast.png.
Needs matplotlib (not an app dependency):  pip install matplotlib pandas pyarrow
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SITES = [("Laoag, Ilocos Norte", "Laoag"), ("Mactan, Cebu", "Mactan"), ("General Santos City", "General Santos")]

hourly = pd.read_parquet(ROOT / "data/rolling/rolling_hourly_combined.parquet")
hourly = hourly[hourly["fold"].astype(str) == "rolling_2026"].copy()
hourly["day"] = hourly["target_timestamp_pht"].dt.tz_localize(None).dt.normalize()

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold"})
fig, axes = plt.subplots(3, 1, figsize=(4.2, 2.75), sharex=True)
for ax, (site, name) in zip(axes, SITES):
    part = hourly[hourly["location"].astype(str) == site]
    daily = part.groupby("day")[["reference_output_mw", "xgboost_prediction_mw"]].sum()
    mae = (part["xgboost_prediction_mw"] - part["reference_output_mw"]).abs().mean()
    ax.plot(daily.index, daily["reference_output_mw"], color="#222222", lw=.9, label="Computed (2026 weather)")
    ax.plot(daily.index, daily["xgboost_prediction_mw"], color="#2b728c", lw=.9, label="XGBoost forecast")
    ax.text(.01, .97, name, transform=ax.transAxes, ha="left", va="top", fontsize=8, fontweight="bold")
    ax.text(.99, .97, f"hourly MAE {mae:.4f} MW", transform=ax.transAxes, ha="right", va="top", fontsize=7, color="#444444")
    ax.set_ylabel("MWh/day", fontsize=7)
    ax.tick_params(labelsize=7)
    ax.set_ylim(0, daily.to_numpy().max() * 1.28)
    ax.grid(axis="y", color="#eeeeee", lw=.8)
axes[-1].xaxis.set_major_locator(mdates.MonthLocator())
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
axes[-1].set_xlabel("Target day, 2026", fontsize=7)
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, fontsize=7.5, bbox_to_anchor=(.53, 1.0))
fig.tight_layout(rect=(0, 0, 1, .95), h_pad=.4)
out = ROOT / "paper/fig_2026_computed_vs_forecast.png"
fig.savefig(out, dpi=300)
print("wrote", out)
