"""Cached data access and the live simulation used by every page."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from solwind.dispatch import simulate_battery, synthetic_load_mw
from solwind.physics import ASSUMPTIONS, load_power_curve, pv_output, wind_output

DATA = Path(__file__).resolve().parents[1] / "data"

SITES = ["Laoag, Ilocos Norte", "Mactan, Cebu", "General Santos City"]
SITE_SHORT = {
    "Laoag, Ilocos Norte": "Laoag",
    "Mactan, Cebu": "Mactan",
    "General Santos City": "General Santos",
}
SITE_ISLAND = {
    "Laoag, Ilocos Norte": "Luzon · 18.2°N",
    "Mactan, Cebu": "Visayas · 10.3°N",
    "General Santos City": "Mindanao · 6.1°N",
}
SITE_BLURB = {
    "Laoag, Ilocos Norte": "Northern Luzon coast. Strong Amihan winds from November to March.",
    "Mactan, Cebu": "Central Visayas island. A balanced mix of sun and sea breeze.",
    "General Santos City": "Southern Mindanao. Sheltered from typhoon tracks, sun-dominant.",
}
MODELS = ["xgboost", "previous_day", "training_climatology"]
MODEL_LABEL = {
    "xgboost": "XGBoost",
    "previous_day": "Previous day",
    "training_climatology": "Past average",
}

# Defaults reproduce the paper's standardized 1 MW + 1 MW system.
DEFAULTS = {
    "site": SITES[0],
    "solar_capacity": 1.0,
    "wind_capacity": 1.0,
    "battery_capacity": 2.0,
    "load_scale": 1.0,
    "solar_loss": ASSUMPTIONS["pv_system_loss_fraction"],
    "temperature_coefficient": ASSUMPTIONS["pv_temperature_coefficient_per_c"],
    "wind_shear": ASSUMPTIONS["wind_shear_exponent"],
    "wind_net_factor": ASSUMPTIONS["wind_net_output_factor"],
}


HOURS_PER_YEAR = 8766  # 365.25 days


def years_in(frame: pd.DataFrame) -> float:
    """Length of a one-site hourly record in years (Jan 2020 to Jun 2026 is about 6.5)."""
    return len(frame) / HOURS_PER_YEAR


def settings() -> dict:
    """Current system design, shared across pages through session state."""
    return {key: st.session_state.get(key, value) for key, value in DEFAULTS.items()}


@st.cache_data(show_spinner=False)
def load_weather() -> pd.DataFrame:
    """Hourly NASA POWER weather, 1 Jan 2020 to 30 Jun 2026 (see scripts/extend_weather.py)."""
    return pd.read_parquet(DATA / "weather_hourly.parquet")


@st.cache_data(show_spinner=False)
def load_predictions() -> pd.DataFrame:
    return pd.read_parquet(DATA / "forecast_predictions_2025.parquet")


@st.cache_data(show_spinner=False)
def load_metrics() -> pd.DataFrame:
    return pd.read_csv(DATA / "test_metrics_2025.csv")


@st.cache_data(show_spinner=False)
def load_replay() -> pd.DataFrame:
    return pd.read_parquet(DATA / "day_ahead_replay_2025.parquet")


@st.cache_data(show_spinner=False)
def load_plan_summary() -> pd.DataFrame:
    return pd.read_csv(DATA / "day_ahead_simulation_2025_summary.csv")


@st.cache_data(show_spinner=False)
def load_site_summary() -> pd.DataFrame:
    return pd.read_csv(DATA / "site_summary.csv")


@st.cache_data(show_spinner="Running the solar and wind equations over 170,856 site-hours…")
def run_generation(
    solar_loss: float,
    temperature_coefficient: float,
    wind_shear: float,
    wind_net_factor: float,
    solar_capacity: float,
    wind_capacity: float,
) -> pd.DataFrame:
    weather = load_weather()
    solar = pv_output(weather, solar_loss, temperature_coefficient)
    wind = wind_output(weather, load_power_curve(), wind_shear, wind_net_factor)
    result = weather[["location", "timestamp_pht", "cloud_amount_pct", "wind_direction_50m_deg"]].copy()
    result["solar_mw"] = solar["solar_output_mw"] * solar_capacity
    result["wind_mw"] = wind["wind_output_mw"] * wind_capacity
    result["combined_mw"] = result["solar_mw"] + result["wind_mw"]
    result["hub_wind_m_s"] = wind["wind_speed_69m_m_s"]
    result["poa_w_m2"] = solar["plane_of_array_irradiance_wh_m2"]
    return result


@st.cache_data(show_spinner="Dispatching the battery hour by hour…")
def run_dispatch(
    site: str,
    load_scale: float,
    battery_capacity: float,
    **physics: float,
) -> pd.DataFrame:
    generation = run_generation(**physics)
    result = (
        generation.loc[generation["location"] == site]
        .sort_values("timestamp_pht")
        .reset_index(drop=True)
    )
    result["demand_mw"] = synthetic_load_mw(result["timestamp_pht"].dt.hour) * load_scale
    dispatch = simulate_battery(
        result["combined_mw"].to_numpy(),
        result["demand_mw"].to_numpy(),
        battery_capacity,
    )
    return pd.concat([result, dispatch], axis=1)


def physics_args(cfg: dict) -> dict:
    return {
        key: cfg[key]
        for key in [
            "solar_loss",
            "temperature_coefficient",
            "wind_shear",
            "wind_net_factor",
            "solar_capacity",
            "wind_capacity",
        ]
    }


def current_generation() -> pd.DataFrame:
    return run_generation(**physics_args(settings()))


def current_dispatch(site: str | None = None) -> pd.DataFrame:
    cfg = settings()
    return run_dispatch(
        site or cfg["site"], cfg["load_scale"], cfg["battery_capacity"], **physics_args(cfg)
    )


@st.cache_data(show_spinner=False, max_entries=8)
def dispatch_csv(site: str, load_scale: float, battery_capacity: float, **physics: float) -> bytes:
    columns = [
        "timestamp_pht", "solar_mw", "wind_mw", "combined_mw", "demand_mw",
        "battery_soc_end_mwh", "grid_import_mwh", "curtailed_renewable_mwh",
    ]
    return run_dispatch(site, load_scale, battery_capacity, **physics)[columns].to_csv(index=False).encode()


def coverage_pct(frame: pd.DataFrame) -> float:
    served = frame["renewable_to_load_mwh"].sum() + frame["battery_discharge_to_load_mwh"].sum()
    return float(100 * served / frame["demand_mw"].sum())


def headline_findings() -> dict:
    """Numbers quoted on the overview page, derived from the stored results."""
    metrics = load_metrics()
    overall = metrics.loc[
        (metrics["scope"] == "all_hours")
        & (metrics["aggregation"] == "overall")
        & (metrics["source"] == "combined")
    ].pivot(index="location", columns="model", values="mae_mw")
    best_baseline = overall[["previous_day", "training_climatology"]].min(axis=1)
    mae_cut = 100 * (1 - overall["xgboost"] / best_baseline)

    plans = load_plan_summary().pivot(
        index="location", columns="model", values="total_grid_adjustment_mwh"
    )
    plan_baseline = plans[["previous_day", "training_climatology"]].min(axis=1)
    plan_cut = 100 * (1 - plans["xgboost"] / plan_baseline)

    return {
        "xgb_wins_everywhere": bool((overall["xgboost"] < best_baseline).all()),
        "mae_cut_min": float(mae_cut.min()),
        "mae_cut_max": float(mae_cut.max()),
        "plan_cut_min": float(plan_cut.min()),
        "plan_cut_max": float(plan_cut.max()),
        "test_hours": int(load_predictions().groupby(["location", "target_timestamp_pht"]).ngroups),
        "mae_cut": mae_cut,
        "plan_cut": plan_cut,
    }


def monthly_profile(frame: pd.DataFrame, column: str = "combined_mw") -> np.ndarray:
    return frame.groupby(frame["timestamp_pht"].dt.month)[column].mean().to_numpy()


# Chronological (rolling-year) evaluation produced by the research team. See scripts/build_rolling.py.
ROLLING = DATA / "rolling"
FOLDS = ["rolling_2024", "rolling_2025", "rolling_2026", "recent_2026"]
FOLD_LABEL = {
    "rolling_2024": "2024",
    "rolling_2025": "2025",
    "rolling_2026": "2026 Jan–Jun",
    "recent_2026": "2026 Jan–Jun · recent window",
}
FOLD_WINDOWS = {  # fit, select, refit, test (years)
    "rolling_2024": ((2020, 2022), 2023, (2020, 2023), 2024),
    "rolling_2025": ((2020, 2023), 2024, (2020, 2024), 2025),
    "rolling_2026": ((2020, 2024), 2025, (2020, 2025), 2026),
    "recent_2026": ((2021, 2024), 2025, (2021, 2025), 2026),
}


@st.cache_data(show_spinner=False)
def load_rolling_metrics() -> pd.DataFrame:
    return pd.read_csv(ROLLING / "rolling_metrics.csv")


@st.cache_data(show_spinner=False)
def load_rolling_plan() -> pd.DataFrame:
    return pd.read_csv(ROLLING / "rolling_planning_summary.csv")


@st.cache_data(show_spinner=False)
def load_rolling_bootstrap() -> pd.DataFrame:
    return pd.read_csv(ROLLING / "paired_block_bootstrap.csv")


@st.cache_data(show_spinner=False)
def load_rolling_hourly() -> pd.DataFrame:
    hourly = pd.read_parquet(ROLLING / "rolling_hourly_combined.parquet")
    hourly["fold"] = hourly["fold"].astype(str)
    hourly["location"] = hourly["location"].astype(str)
    return hourly


@st.cache_data(show_spinner=False)
def rolling_daily() -> pd.DataFrame:
    """One row per fold, site and day: combined MAE per method and grid-plan adjustment."""
    hourly = load_rolling_hourly()
    frame = hourly[["fold", "location"]].copy()
    frame["day"] = hourly["target_timestamp_pht"].dt.date
    frame["reference_mwh"] = hourly["reference_output_mw"]
    for model in MODELS:
        frame[f"{model}_mae"] = (hourly[f"{model}_prediction_mw"] - hourly["reference_output_mw"]).abs()
        frame[f"{model}_adjust"] = hourly[f"{model}_adjust_mwh"]
    agg = {c: "mean" for c in frame.columns if c.endswith("_mae")}
    agg.update({c: "sum" for c in frame.columns if c.endswith("_adjust") or c == "reference_mwh"})
    return frame.groupby(["fold", "location", "day"], as_index=False).agg(agg)
