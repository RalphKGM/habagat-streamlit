#!/usr/bin/env python3
"""Package the research project's datasets into the compact files this app reads.

Run once from this folder, pointing at the full research project:

    python scripts/build_data.py ~/Downloads/Solar_Wind_Classroom_Presentation

The app only needs the columns listed below. Parquet keeps the repository small
enough for GitHub and Streamlit Community Cloud while preserving full float64
precision, so the physics reproduces the paper's numbers exactly.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

APP_ROOT = Path(__file__).resolve().parents[1]
OUT = APP_ROOT / "data"

WEATHER_COLUMNS = [
    "timestamp_pht",
    "location",
    "island_group",
    "latitude_deg",
    "longitude_deg",
    "solar_irradiance_wh_m2",
    "direct_normal_irradiance_wh_m2",
    "diffuse_horizontal_irradiance_wh_m2",
    "air_temperature_2m_c",
    "wind_speed_10m_m_s",
    "wind_speed_50m_m_s",
    "wind_direction_50m_deg",
    "surface_pressure_site_corrected_kpa",
    "cloud_amount_pct",
]

PREDICTION_COLUMNS = [
    "target_timestamp_pht",
    "horizon_hour",
    "location",
    "source",
    "reference_output_mw",
    "previous_day_prediction_mw",
    "training_climatology_prediction_mw",
    "xgboost_prediction_mw",
]


def to_manila(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True).dt.tz_convert("Asia/Manila")


def main(source_root: Path) -> None:
    OUT.mkdir(exist_ok=True)

    weather = pd.read_csv(
        source_root
        / "data/nasa_power/processed/nasa_power_hourly_laoag_mactan_gensan_2020_2024_pht_enriched.csv",
        usecols=WEATHER_COLUMNS,
    )
    # Keep the original fixed +08:00 offset: the solar geometry reads local clock hours.
    weather["timestamp_pht"] = pd.to_datetime(weather["timestamp_pht"])
    weather.to_parquet(OUT / "weather_2020_2024.parquet", index=False, compression="zstd")

    predictions = pd.read_csv(
        source_root / "data/forecasting/results/test_predictions_2025.csv",
        usecols=PREDICTION_COLUMNS,
    )
    predictions["target_timestamp_pht"] = to_manila(predictions["target_timestamp_pht"])
    predictions.to_parquet(OUT / "forecast_predictions_2025.parquet", index=False, compression="zstd")

    replay = pd.read_csv(source_root / "data/forecasting/results/day_ahead_simulation_2025_hourly.csv")
    replay = replay.drop(columns=["target_timestamp_pht"])
    replay["timestamp"] = to_manila(replay["timestamp"])
    replay.to_parquet(OUT / "day_ahead_replay_2025.parquet", index=False, compression="zstd")

    for relative in [
        "data/forecasting/results/test_metrics_2025.csv",
        "data/forecasting/results/day_ahead_simulation_2025_summary.csv",
        "data/simulation/results/site_summary.csv",
        "data/simulation/results/demand_coverage_summary.csv",
        "data/model_inputs/raw/EWT_DW61_1MW_60.9.csv",
        "data/model_inputs/raw/EWT_DW61_1MW_60.9.yaml",
        "data/model_inputs/raw/NLR_turbine_models_LICENSE.txt",
    ]:
        shutil.copy2(source_root / relative, OUT / Path(relative).name)

    for path in sorted(OUT.iterdir()):
        print(f"{path.stat().st_size / 1e6:8.2f} MB  {path.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/build_data.py <path to research project>")
    main(Path(sys.argv[1]).expanduser().resolve())
