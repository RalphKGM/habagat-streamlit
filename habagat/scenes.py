"""Data-driven animated scenes rendered in sandboxed iframes."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit.components.v1 as components

from habagat.dispatch import synthetic_load_mw
from habagat.theme import MODEL_COLOR

ASSETS = Path(__file__).resolve().parent / "assets"


def _fill(template: str, **values: str) -> str:
    html = (ASSETS / template).read_text(encoding="utf-8")
    for key, value in values.items():
        html = html.replace(f"__{key}__", value)
    return html


def plant(day: pd.DataFrame, cfg: dict, label: str, start_hour: int = 6, height: int = 600) -> None:
    """Animated plant for one simulated day (24 rows of the dispatch frame)."""
    hours = [
        {
            "solar": round(float(r.solar_mw), 4),
            "wind": round(float(r.wind_mw), 4),
            "hub": round(float(r.hub_wind_m_s), 2),
            "cloud": round(float(r.cloud_amount_pct), 1),
            "demand": round(float(r.demand_mw), 4),
            "soc": round(float(r.battery_soc_end_mwh), 4),
            "charge": round(float(r.battery_charge_input_mwh), 4),
            "discharge": round(float(r.battery_discharge_to_load_mwh), 4),
            "grid": round(float(r.grid_import_mwh), 4),
            "spill": round(float(r.curtailed_renewable_mwh), 4),
            "direct": round(float(r.renewable_to_load_mwh), 4),
        }
        for r in day.itertuples()
    ]
    payload = {
        "label": label,
        "hours": hours,
        "solarCap": cfg["solar_capacity"],
        "windCap": cfg["wind_capacity"],
        "battCap": cfg["battery_capacity"],
        "peakDemand": float(synthetic_load_mw(pd.Series([18])).max() * cfg["load_scale"]),
        "startHour": start_hour,
    }
    components.html(_fill("plant.html", DATA=json.dumps(payload)), height=height)


def replay(day: pd.DataFrame, model: str, model_label: str, label: str, height: int = 380) -> None:
    hours = [
        {
            "ref": round(float(r["reference_output_mw"]), 4),
            "fc": round(float(r[f"{model}_prediction_mw"]), 4),
            "planned": round(float(r[f"{model}_planned_grid_mwh"]), 4),
            "needed": round(float(r["actual_grid_import_mwh"]), 4),
            "extra": round(float(r[f"{model}_extra_grid_mwh"]), 4),
            "unused": round(float(r[f"{model}_unused_grid_plan_mwh"]), 4),
        }
        for _, r in day.iterrows()
    ]
    payload = {"label": label, "hours": hours, "color": MODEL_COLOR[model]}
    components.html(
        _fill("replay.html", DATA=json.dumps(payload), COLOR=MODEL_COLOR[model], MODEL=model_label),
        height=height,
    )
