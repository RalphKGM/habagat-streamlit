"""The app's engine must reproduce the paper's published results exactly.

Run with:  python -m pytest tests -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from habagat.dispatch import simulate_battery, synthetic_load_mw  # noqa: E402
from habagat.physics import ASSUMPTIONS, load_power_curve, pv_output, wind_output  # noqa: E402

SITE_SUMMARY = pd.read_csv(ROOT / "data/site_summary.csv").set_index("location")
COVERAGE = pd.read_csv(ROOT / "data/demand_coverage_summary.csv")


@pytest.fixture(scope="module")
def generation() -> pd.DataFrame:
    weather = pd.read_parquet(ROOT / "data/weather_hourly.parquet")
    weather = weather.loc[weather["timestamp_pht"].dt.year <= 2024].reset_index(drop=True)
    solar = pv_output(
        weather,
        ASSUMPTIONS["pv_system_loss_fraction"],
        ASSUMPTIONS["pv_temperature_coefficient_per_c"],
    )
    wind = wind_output(
        weather,
        load_power_curve(),
        ASSUMPTIONS["wind_shear_exponent"],
        ASSUMPTIONS["wind_net_output_factor"],
    )
    frame = weather[["location", "timestamp_pht"]].copy()
    frame["solar_mw"] = solar["solar_output_mw"]
    frame["wind_mw"] = wind["wind_output_mw"]
    return frame


def test_five_year_energy_matches_paper(generation: pd.DataFrame) -> None:
    totals = generation.groupby("location")[["solar_mw", "wind_mw"]].sum()
    for site, row in totals.iterrows():
        assert row["solar_mw"] == pytest.approx(SITE_SUMMARY.loc[site, "solar_energy_5yr_mwh"], rel=1e-6)
        assert row["wind_mw"] == pytest.approx(SITE_SUMMARY.loc[site, "wind_energy_5yr_mwh"], rel=1e-6)


@pytest.mark.parametrize("battery", [0.0, 2.0, 4.0])
def test_battery_coverage_matches_paper(generation: pd.DataFrame, battery: float) -> None:
    for site, frame in generation.groupby("location"):
        frame = frame.sort_values("timestamp_pht")
        demand = synthetic_load_mw(frame["timestamp_pht"].dt.hour)
        flows = simulate_battery((frame["solar_mw"] + frame["wind_mw"]).to_numpy(), demand, battery)
        coverage = 100 * (
            flows["renewable_to_load_mwh"].sum() + flows["battery_discharge_to_load_mwh"].sum()
        ) / demand.sum()
        expected = COVERAGE.loc[
            (COVERAGE["location"] == site)
            & (COVERAGE["load_scale"] == 1.0)
            & (COVERAGE["battery_capacity_mwh"] == battery),
            "renewable_demand_coverage_pct",
        ].item()
        assert coverage == pytest.approx(expected, abs=1e-4)


def test_extension_years_match_team_reference() -> None:
    # 2025 and Jan-Jun 2026 hours reproduce the research team's modeled output (CSV rounding is 1e-6 MW per hour).
    weather = pd.read_parquet(ROOT / "data/weather_hourly.parquet")
    weather = weather.loc[weather["timestamp_pht"].dt.year >= 2025].reset_index(drop=True)
    solar = pv_output(weather, ASSUMPTIONS["pv_system_loss_fraction"], ASSUMPTIONS["pv_temperature_coefficient_per_c"])
    wind = wind_output(weather, load_power_curve(), ASSUMPTIONS["wind_shear_exponent"], ASSUMPTIONS["wind_net_output_factor"])
    frame = weather[["location"]].copy()
    frame["period"] = weather["timestamp_pht"].dt.year.map({2025: "2025", 2026: "2026H1"})
    frame["solar_energy_mwh"] = solar["solar_output_mw"]
    frame["wind_energy_mwh"] = wind["wind_output_mw"]
    ours = frame.groupby(["period", "location"]).sum()
    ref = pd.read_csv(ROOT / "data/reference_totals_2025_2026.csv").set_index(["period", "location"])
    hours = frame.groupby(["period", "location"]).size()
    for key, row in ref.iterrows():
        for col in ["solar_energy_mwh", "wind_energy_mwh"]:
            assert abs(ours.loc[key, col] - row[col]) <= hours.loc[key] * 1e-6
