"""Interactive island-group map (two-way Streamlit component, plain HTML/JS in assets/map)."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from habagat.daypicker import daily_series
from habagat.data import (
    SITE_SHORT,
    SITES,
    coverage_pct,
    current_dispatch,
    current_generation,
    headline_findings,
    load_metrics,
    load_plan_summary,
    load_weather,
    settings,
    years_in,
)

ASSETS = Path(__file__).resolve().parent / "assets"
_map = components.declare_component("habagat_map", path=str(ASSETS / "map"))
GROUP = {"Laoag, Ilocos Norte": "Luzon", "Mactan, Cebu": "Visayas", "General Santos City": "Mindanao"}


@st.cache_data(show_spinner=False)
def _outlines() -> dict:
    return json.loads((ASSETS / "ph_map.json").read_text())


def _site_summaries() -> dict:
    cfg = settings()
    generation = current_generation()
    weather = load_weather().drop_duplicates("location").set_index("location")
    metrics = load_metrics()
    mae = metrics.loc[(metrics["scope"] == "all_hours") & (metrics["aggregation"] == "overall")
                      & (metrics["source"] == "combined")].set_index(["location", "model"])["mae_mw"]
    adj = load_plan_summary().set_index(["location", "model"])["total_grid_adjustment_mwh"]
    found = headline_findings()
    cap = max(cfg["solar_capacity"] + cfg["wind_capacity"], 1e-9)
    out = {}
    for site in SITES:
        g = generation.loc[generation["location"] == site]
        d = current_dispatch(site)
        years = years_in(g)
        solar, wind = g["solar_mw"].sum(), g["wind_mw"].sum()
        models = ["xgboost", "previous_day", "training_climatology"]
        out[site] = {
            "short": SITE_SHORT[site],
            "group": GROUP[site],
            "lat": float(weather.loc[site, "latitude_deg"]),
            "lon": float(weather.loc[site, "longitude_deg"]),
            "annual": float((solar + wind) / years),
            "cf": float(g["combined_mw"].mean() / cap),
            "wind_share": float(wind / (solar + wind)) if solar + wind else 0.0,
            "coverage": coverage_pct(d),
            "grid": float(d["grid_import_mwh"].sum() / years),
            "forecast": {
                "mae": {m: float(mae.loc[(site, m)]) for m in models},
                "adj": {m: float(adj.loc[(site, m)]) for m in models},
                "mae_cut": float(found["mae_cut"].loc[site]),
                "plan_cut": float(found["plan_cut"].loc[site]),
            },
        }
    return out


def _day(site: str, day: dt.date) -> tuple[list, dict]:
    d = current_dispatch(site)
    rows = d.loc[d["timestamp_pht"].dt.date == day]
    hours = [
        {
            "s": round(float(r.solar_mw), 4), "w": round(float(r.wind_mw), 4), "d": round(float(r.demand_mw), 4),
            "soc": round(float(r.battery_soc_end_mwh), 4), "dis": round(float(r.battery_discharge_to_load_mwh), 4),
            "g": round(float(r.grid_import_mwh), 4), "sp": round(float(r.curtailed_renewable_mwh), 4),
            "hub": round(float(r.hub_wind_m_s), 2), "dir": round(float(r.wind_direction_50m_deg), 1),
        }
        for r in rows.itertuples()
    ]
    served = rows["renewable_to_load_mwh"].sum() + rows["battery_discharge_to_load_mwh"].sum()
    return hours, {"share": float(served / rows["demand_mw"].sum()), "gen": float(rows["combined_mw"].sum())}


def render(key: str = "map") -> None:
    cfg = settings()
    st.session_state.setdefault("plant_date", dt.date(2022, 9, 15))
    day = st.session_state.plant_date
    days, summaries = {}, {}
    for site in SITES:
        days[site], summaries[site] = _day(site, day)
    stamps = current_dispatch(SITES[0])["timestamp_pht"]
    data = {
        "map": _outlines(),
        "sites": _site_summaries(),
        "day": days,
        "daySummary": summaries,
        "date": day.isoformat(),
        "dateLabel": f"{day:%a %d %b %Y}",
        "minDate": stamps.min().date().isoformat(),
        "maxDate": stamps.max().date().isoformat(),
        "selected": cfg["site"],
        "daily": daily_series(cfg["site"]),
        "startHour": 13,
        "cfg": {"solar": cfg["solar_capacity"], "wind": cfg["wind_capacity"], "batt": cfg["battery_capacity"]},
    }
    event = _map(data=data, key=key, default=None)
    # Apply each click / date change once; the component keeps returning its last value.
    if event and event.get("nonce") != st.session_state.get("_map_nonce"):
        st.session_state._map_nonce = event["nonce"]
        changed = False
        if event.get("site") in SITES and event["site"] != st.session_state.site:
            st.session_state.site = event["site"]
            changed = True
        new_day = pd.Timestamp(event.get("date")).date() if event.get("date") else day
        if new_day != day:
            st.session_state.plant_date = new_day
            changed = True
        if changed:
            st.rerun()
