#!/usr/bin/env python3
"""Package the team's chronological (rolling-year) evaluation for the Rolling test page.

Run from this folder, pointing at the project that holds data/forecasting/rolling:

    python scripts/build_rolling.py "~/Desktop/final-submission-simulation/[3 - STREAMLIT]/project"

Writes small summary CSVs plus one hourly parquet of combined (solar + wind) output
for every test fold, so a viewer can open any day of 2024, 2025 or January-June 2026.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

APP_ROOT = Path(__file__).resolve().parents[1]
OUT = APP_ROOT / "data" / "rolling"
FOLDS = ["rolling_2024", "rolling_2025", "rolling_2026", "recent_2026"]
MODELS = ["previous_day", "training_climatology", "xgboost"]


def main(project: Path) -> None:
    results = project / "data/forecasting/rolling/results"
    OUT.mkdir(parents=True, exist_ok=True)

    metrics = pd.read_csv(results / "rolling_metrics.csv")
    keep = (metrics["scope"].isin(["all_hours", "daylight"])) & (metrics["aggregation"].isin(["overall", "horizon", "month"]))
    metrics.loc[keep].to_csv(OUT / "rolling_metrics.csv", index=False)
    for name in ["rolling_planning_summary.csv", "paired_block_bootstrap.csv", "rolling_selection.csv"]:
        shutil.copy2(results / name, OUT / name)

    frames = []
    for fold in FOLDS:
        pred = pd.read_csv(results / f"{fold}_predictions.csv")
        # The research outputs already carry a "combined" source (solar + wind).
        combined = pred.loc[
            pred["source"] == "combined",
            ["location", "target_timestamp_pht", "reference_output_mw"] + [f"{m}_prediction_mw" for m in MODELS],
        ]
        plan = pd.read_csv(
            results / f"{fold}_planning_hourly.csv",
            usecols=["location", "target_timestamp_pht"]
            + [f"{m}_{k}" for m in MODELS for k in ["extra_grid_mwh", "unused_grid_plan_mwh"]],
        )
        for m in MODELS:
            plan[f"{m}_adjust_mwh"] = plan.pop(f"{m}_extra_grid_mwh") + plan.pop(f"{m}_unused_grid_plan_mwh")
        hourly = combined.merge(plan, on=["location", "target_timestamp_pht"], validate="one_to_one")
        hourly.insert(0, "fold", fold)
        frames.append(hourly)
    hourly = pd.concat(frames, ignore_index=True)
    hourly["target_timestamp_pht"] = pd.to_datetime(hourly["target_timestamp_pht"], utc=True).dt.tz_convert("Asia/Manila")
    hourly["fold"] = hourly["fold"].astype("category")
    hourly["location"] = hourly["location"].astype("category")
    hourly.to_parquet(OUT / "rolling_hourly_combined.parquet", index=False, compression="zstd")

    for qa in ["data_coverage_2026.json", "rolling_verification.json"]:
        shutil.copy2(project / "data/forecasting/rolling/qa" / qa, OUT / qa)

    for path in sorted(OUT.iterdir()):
        print(f"{path.stat().st_size / 1e6:8.2f} MB  {path.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/build_rolling.py <path to project with data/forecasting/rolling>")
    main(Path(sys.argv[1]).expanduser().resolve())
