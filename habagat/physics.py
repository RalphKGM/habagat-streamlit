"""Solar PV and wind turbine physics.

Copied verbatim from the research project's ``src/run_renewable_simulation.py``
(solar_geometry, pv_output, load_power_curve, wind_output, ASSUMPTIONS) so the app
reproduces the paper's reference modeled output. ``tests/test_engine.py`` checks
the results against the published site summary.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

MODEL_INPUTS = Path(__file__).resolve().parents[1] / "data"

ASSUMPTIONS = {
    "pv_dc_capacity_mw": 1.0,
    "pv_ac_limit_mw": 1.0,
    "pv_fixed_tilt_deg": 10.0,
    "pv_azimuth_deg": 180.0,
    "ground_albedo": 0.20,
    "pv_temperature_coefficient_per_c": -0.0047,
    "pv_reference_temperature_c": 25.0,
    "pv_reference_irradiance_w_m2": 1000.0,
    "pv_system_loss_fraction": 0.14,
    "pv_inverter_efficiency": 0.96,
    "faiman_u0_w_m2_c": 25.0,
    "faiman_u1_w_s_m3_c": 6.84,
    "pv_module_wind_height_m": 2.0,
    "wind_turbine_model": "EWT DW61 1MW",
    "wind_turbine_capacity_mw": 1.0,
    "wind_hub_height_m": 69.0,
    "wind_source_height_m": 50.0,
    "wind_shear_exponent": 0.14,
    "wind_reference_air_density_kg_m3": 1.225,
    "wind_net_output_factor": 0.90,
    "low_output_threshold_fraction": 0.10,
    "philippine_timezone_utc_offset_hours": 8,
}


def solar_geometry(
    local_time: pd.Series, latitude: np.ndarray, longitude: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """NOAA fractional-year approximation at each hourly interval midpoint."""
    dt = pd.to_datetime(local_time)
    midpoint_hour = dt.dt.hour.to_numpy(dtype=float) + 0.5
    days_in_year = np.where(dt.dt.is_leap_year.to_numpy(), 366.0, 365.0)
    gamma = (
        2.0
        * np.pi
        / days_in_year
        * (
            dt.dt.dayofyear.to_numpy()
            - 1.0
            + (midpoint_hour - 12.0) / 24.0
        )
    )
    eqtime = 229.18 * (
        0.000075
        + 0.001868 * np.cos(gamma)
        - 0.032077 * np.sin(gamma)
        - 0.014615 * np.cos(2.0 * gamma)
        - 0.040849 * np.sin(2.0 * gamma)
    )
    decl = (
        0.006918
        - 0.399912 * np.cos(gamma)
        + 0.070257 * np.sin(gamma)
        - 0.006758 * np.cos(2.0 * gamma)
        + 0.000907 * np.sin(2.0 * gamma)
        - 0.002697 * np.cos(3.0 * gamma)
        + 0.00148 * np.sin(3.0 * gamma)
    )
    time_offset = (
        eqtime
        + 4.0 * longitude
        - 60.0 * ASSUMPTIONS["philippine_timezone_utc_offset_hours"]
    )
    true_solar_minutes = np.mod(midpoint_hour * 60.0 + time_offset, 1440.0)
    hour_angle = np.deg2rad(true_solar_minutes / 4.0 - 180.0)
    lat_rad = np.deg2rad(latitude)
    cos_zenith = np.clip(
        np.sin(lat_rad) * np.sin(decl)
        + np.cos(lat_rad) * np.cos(decl) * np.cos(hour_angle),
        -1.0,
        1.0,
    )
    zenith_deg = np.rad2deg(np.arccos(cos_zenith))
    return decl, hour_angle, zenith_deg


def pv_output(
    frame: pd.DataFrame, system_loss_fraction: float, gamma_pdc: float
) -> dict[str, np.ndarray]:
    ghi = frame["solar_irradiance_wh_m2"].to_numpy(dtype=float).clip(min=0.0)
    dni = frame["direct_normal_irradiance_wh_m2"].to_numpy(dtype=float).clip(min=0.0)
    dhi = (
        frame["diffuse_horizontal_irradiance_wh_m2"]
        .to_numpy(dtype=float)
        .clip(min=0.0)
    )
    temp = frame["air_temperature_2m_c"].to_numpy(dtype=float)
    wind10 = frame["wind_speed_10m_m_s"].to_numpy(dtype=float).clip(min=0.0)
    lat = frame["latitude_deg"].to_numpy(dtype=float)
    lon = frame["longitude_deg"].to_numpy(dtype=float)

    decl, hour_angle, zenith = solar_geometry(
        frame["timestamp_pht"], lat, lon
    )
    beta = math.radians(ASSUMPTIONS["pv_fixed_tilt_deg"])
    lat_rad = np.deg2rad(lat)
    cos_incidence = (
        np.sin(decl) * np.sin(lat_rad - beta)
        + np.cos(decl)
        * np.cos(lat_rad - beta)
        * np.cos(hour_angle)
    )
    sun_up = zenith < 90.0
    poa_direct = dni * np.maximum(cos_incidence, 0.0) * sun_up
    poa_sky = dhi * (1.0 + math.cos(beta)) / 2.0
    poa_ground = (
        ghi
        * ASSUMPTIONS["ground_albedo"]
        * (1.0 - math.cos(beta))
        / 2.0
    )
    poa = np.maximum(poa_direct + poa_sky + poa_ground, 0.0)
    poa = np.where((ghi <= 0.0) & (dhi <= 0.0), 0.0, poa)

    module_wind = wind10 * (
        ASSUMPTIONS["pv_module_wind_height_m"] / 10.0
    ) ** ASSUMPTIONS["wind_shear_exponent"]
    cell_temp = temp + poa / (
        ASSUMPTIONS["faiman_u0_w_m2_c"]
        + ASSUMPTIONS["faiman_u1_w_s_m3_c"] * module_wind
    )
    temperature_factor = np.maximum(
        0.0,
        1.0
        + gamma_pdc
        * (cell_temp - ASSUMPTIONS["pv_reference_temperature_c"]),
    )
    dc_mw = (
        ASSUMPTIONS["pv_dc_capacity_mw"]
        * (poa / ASSUMPTIONS["pv_reference_irradiance_w_m2"])
        * temperature_factor
    )
    dc_mw = np.maximum(dc_mw, 0.0)
    ac_mw = (
        dc_mw
        * (1.0 - system_loss_fraction)
        * ASSUMPTIONS["pv_inverter_efficiency"]
    )
    ac_mw = np.clip(ac_mw, 0.0, ASSUMPTIONS["pv_ac_limit_mw"])
    ac_mw = np.where(poa <= 0.0, 0.0, ac_mw)
    return {
        "solar_zenith_midpoint_deg": zenith,
        "plane_of_array_irradiance_wh_m2": poa,
        "estimated_pv_cell_temperature_c": cell_temp,
        "solar_dc_gross_mw": dc_mw,
        "solar_output_mw": ac_mw,
    }


def load_power_curve() -> pd.DataFrame:
    curve = pd.read_csv(MODEL_INPUTS / "EWT_DW61_1MW_60.9.csv")
    curve = curve.rename(
        columns={
            "Wind Speed [m/s]": "wind_speed_m_s",
            "Power [kW]": "power_kw",
            "Cp [-]": "cp",
        }
    )
    curve = curve.dropna(subset=["wind_speed_m_s", "power_kw"]).copy()
    return curve.astype(
        {"wind_speed_m_s": float, "power_kw": float, "cp": float}
    )


def wind_output(
    frame: pd.DataFrame,
    curve: pd.DataFrame,
    shear_exponent: float,
    net_factor: float,
) -> dict[str, np.ndarray]:
    wind50 = frame["wind_speed_50m_m_s"].to_numpy(dtype=float).clip(min=0.0)
    pressure_pa = (
        frame["surface_pressure_site_corrected_kpa"].to_numpy(dtype=float)
        * 1000.0
    )
    temp_k = frame["air_temperature_2m_c"].to_numpy(dtype=float) + 273.15
    hub_speed = wind50 * (
        ASSUMPTIONS["wind_hub_height_m"]
        / ASSUMPTIONS["wind_source_height_m"]
    ) ** shear_exponent
    air_density = pressure_pa / (287.05 * temp_k)
    density_adjusted = hub_speed * (
        air_density / ASSUMPTIONS["wind_reference_air_density_kg_m3"]
    ) ** (1.0 / 3.0)
    speed_points = curve["wind_speed_m_s"].to_numpy(dtype=float)
    power_points = curve["power_kw"].to_numpy(dtype=float)
    gross_kw = np.interp(
        density_adjusted,
        speed_points,
        power_points,
        left=0.0,
        right=power_points[-1],
    )
    gross_kw = np.where(density_adjusted > speed_points[-1], 0.0, gross_kw)
    gross_mw = gross_kw / 1000.0
    net_mw = np.clip(
        gross_mw * net_factor,
        0.0,
        ASSUMPTIONS["wind_turbine_capacity_mw"],
    )
    return {
        "wind_speed_69m_m_s": hub_speed,
        "air_density_kg_m3": air_density,
        "density_adjusted_wind_speed_m_s": density_adjusted,
        "wind_gross_mw": gross_mw,
        "wind_output_mw": net_mw,
    }


