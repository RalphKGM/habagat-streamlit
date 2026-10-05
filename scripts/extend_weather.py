#!/usr/bin/env python3
"""Append the 2025 and January-June 2026 NASA POWER hours to the app's weather file.

    python scripts/extend_weather.py "~/Desktop/final-submission-simulation/[3 - STREAMLIT]/project"

The paper's physical study stays 2020-2024 (see habagat.data.STUDY_YEARS); the extra hours
let the Map and Live plant replay any day up to 30 June 2026, the last day with complete
solar inputs when the data were downloaded.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

APP_ROOT = Path(__file__).resolve().parents[1]
OUT = APP_ROOT / "data" / "weather_hourly.parquet"
EXTRA = [
    "data/forecasting/processed/hourly_weather_2025_pht.csv",
    "data/forecasting/rolling/processed/hourly_weather_2026_available_pht.csv",
]


def main(project: Path) -> None:
    # build_data.py writes weather_2020_2024.parquet; rerunning this script starts from the study years.
    first = APP_ROOT / "data" / "weather_2020_2024.parquet"
    base = pd.read_parquet(first if first.exists() else OUT)
    base = base.loc[base["timestamp_pht"].dt.year <= 2024]
    frames = [base]
    for relative in EXTRA:
        extra = pd.read_csv(project / relative, usecols=list(base.columns))
        extra["timestamp_pht"] = pd.to_datetime(extra["timestamp_pht"])
        frames.append(extra[base.columns])
    weather = pd.concat(frames, ignore_index=True).sort_values(["location", "timestamp_pht"], kind="stable")
    weather = weather.reset_index(drop=True)
    assert not weather.duplicated(["location", "timestamp_pht"]).any()
    assert not weather.isna().any().any()
    for _, g in weather.groupby("location"):
        gaps = g["timestamp_pht"].diff().dropna()
        assert (gaps == pd.Timedelta(hours=1)).all(), "hours must be consecutive"
    weather.to_parquet(OUT, index=False, compression="zstd")
    first.unlink(missing_ok=True)
    print(f"{OUT.name}: {len(weather):,} rows, {weather['timestamp_pht'].min()} to {weather['timestamp_pht'].max()}, "
          f"{OUT.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/extend_weather.py <project with data/forecasting>")
    main(Path(sys.argv[1]).expanduser().resolve())
