from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from habagat import theme, ui
from habagat.daypicker import day_picker
from habagat.data import (
    DEFAULTS,
    SITE_SHORT,
    coverage_pct,
    current_dispatch,
    dispatch_csv,
    physics_args,
    run_dispatch,
    settings,
    years_in,
)

theme.header('System designer', 'Change the plant and rerun every hour from January 2020 to June 2026. Differences are shown against the standard design: 1 MW solar, 1 MW wind and a 2 MWh battery.')


def _reset() -> None:
    for key, value in DEFAULTS.items():
        if key != "site":
            st.session_state[key] = value


controls, results = st.columns([1, 2.1], gap="large")
with controls:
    with st.container(border=True):
        site = ui.site_picker()
        st.slider("Solar capacity · MW", 0.0, 3.0, step=0.25, key="solar_capacity")
        st.slider("Wind capacity · MW", 0.0, 3.0, step=0.25, key="wind_capacity")
        st.slider("Battery · MWh", 0.0, 8.0, step=0.5, key="battery_capacity")
        st.slider("Demand multiplier", 0.5, 1.5, step=0.1, key="load_scale")
        with st.expander("Engineering assumptions"):
            st.slider("Other PV losses", 0.05, 0.25, step=0.01, key="solar_loss")
            st.slider("PV temperature coefficient · /°C", -0.0060, -0.0020, step=0.0001, format="%.4f",
                      key="temperature_coefficient")
            st.slider("Wind-shear exponent", 0.08, 0.30, step=0.01, key="wind_shear")
            st.slider("Wind net-output factor", 0.70, 1.00, step=0.01, key="wind_net_factor")
        st.button("Reset to standard design", on_click=_reset, icon=":material/restart_alt:", width="stretch")

cfg = settings()
full = dispatch = current_dispatch(site)
baseline = run_dispatch(site, DEFAULTS["load_scale"], DEFAULTS["battery_capacity"], **physics_args(DEFAULTS))
years = years_in(dispatch)


def delta(value: float, fmt: str) -> str | None:
    return None if abs(value) < 0.05 else format(value, fmt)


def per_year(frame: pd.DataFrame, column: str) -> float:
    return frame[column].sum() / years


with results:
    k = st.columns(2)
    cov, base_cov = coverage_pct(dispatch), coverage_pct(baseline)
    gen, base_gen = per_year(dispatch, "combined_mw"), per_year(baseline, "combined_mw")
    grid, base_grid = per_year(dispatch, "grid_import_mwh"), per_year(baseline, "grid_import_mwh")
    spill, base_spill = per_year(dispatch, "curtailed_renewable_mwh"), per_year(baseline, "curtailed_renewable_mwh")
    k[0].metric("Demand met by renewables", f"{cov:.1f}%", delta(cov - base_cov, "+.1f"))
    k[1].metric("Renewable energy", f"{gen:,.0f} MWh/yr", delta(gen - base_gen, "+,.0f"))
    k = st.columns(2)
    k[0].metric("Grid energy needed", f"{grid:,.0f} MWh/yr", delta(grid - base_grid, "+,.0f"), delta_color="inverse")
    k[1].metric("Unused renewables", f"{spill:,.0f} MWh/yr", delta(spill - base_spill, "+,.0f"), delta_color="inverse")

    yearly = dispatch.groupby(dispatch["timestamp_pht"].dt.year).agg(
        direct=("renewable_to_load_mwh", "sum"),
        battery=("battery_discharge_to_load_mwh", "sum"),
        grid=("grid_import_mwh", "sum"),
    )
    fig = go.Figure()
    for col, name, color in [("direct", "Renewables → load", theme.LEAF), ("battery", "Battery → load", theme.VIOLET),
                             ("grid", "Grid → load", theme.EMBER)]:
        fig.add_bar(x=[f"{y} (Jan–Jun)" if y == 2026 else str(y) for y in yearly.index], y=yearly[col], name=name, marker_color=color)
    fig.update_layout(barmode="stack", bargap=.35)
    fig.update_xaxes(type="category")
    theme.chart(theme.style(fig, f"Where {SITE_SHORT[site]}’s demand was met, by year", "MWh", 330), key="yearly")

theme.section('Average surplus by month and hour', 'Renewable output minus demand, before the battery. Green hours charge the battery and red hours drain it.')
net = dispatch.assign(
    month=dispatch["timestamp_pht"].dt.month,
    hour=dispatch["timestamp_pht"].dt.hour,
    net=dispatch["combined_mw"] - dispatch["demand_mw"],
).pivot_table(index="month", columns="hour", values="net", aggfunc="mean")
limit = float(np.abs(net.to_numpy()).max()) or 1.0
heat = go.Figure(
    go.Heatmap(
        z=net.to_numpy(),
        x=[f"{h:02d}" for h in net.columns],
        y=theme.MONTHS,
        zmin=-limit, zmax=limit,
        colorscale=theme.DIVERGING,
        xgap=2, ygap=2,
        colorbar=dict(title=dict(text="MW", font=dict(family=theme.FONT_MONO, size=11)), thickness=10, outlinewidth=0,
                      tickfont=dict(family=theme.FONT_MONO, size=10)),
        hovertemplate="%{y} · %{x}:00<br>net %{z:+.2f} MW<extra></extra>",
    )
)
heat.update_yaxes(autorange="reversed", ticks="")
heat.update_xaxes(ticks="", title="Hour of day")
heat.update_layout(hovermode="closest")
theme.chart(theme.style(heat, "", "", 380), key="fingerprint")

theme.section('Outage test', 'The grid is unavailable during the selected window, so any shortfall becomes unmet demand.')
outage_day = day_picker("outage_day", site, dt.date(2022, 9, 15), key="outage_picker")
o = st.columns(2)
outage_start = o[0].slider("Starts at", 0, 23, 18, format="%d:00", key="outage_start")
outage_len = o[1].slider("Lasts · hours", 1, 24, 6, key="outage_len")

begin = pd.Timestamp(outage_day).tz_localize(dispatch["timestamp_pht"].dt.tz) + pd.Timedelta(hours=outage_start)
window = full.loc[
    (full["timestamp_pht"] >= begin) & (full["timestamp_pht"] < begin + pd.Timedelta(hours=outage_len))
]
need = window["demand_mw"].sum()
unmet = window["grid_import_mwh"].sum()
served = 100 * (need - unmet) / need if need else 100.0
lights_out = window.loc[window["grid_import_mwh"] > 1e-6, "timestamp_pht"]
r = st.columns(3)
r[0].metric("Demand served in outage", f"{served:.0f}%")
r[1].metric("Unmet demand", f"{unmet:.2f} MWh")
r[2].metric("First shortfall", "None" if lights_out.empty else f"{lights_out.iloc[0]:%H:%M}")

span = full.loc[
    (full["timestamp_pht"] >= begin - pd.Timedelta(hours=6))
    & (full["timestamp_pht"] < begin + pd.Timedelta(hours=outage_len + 6))
]
drill = go.Figure()
drill.add_vrect(x0=begin, x1=begin + pd.Timedelta(hours=outage_len), fillcolor=theme.EMBER, opacity=.09, line_width=0,
                annotation_text="GRID DOWN", annotation_position="top left",
                annotation_font=dict(family=theme.FONT_MONO, size=10, color=theme.EMBER))
drill.add_scatter(x=span["timestamp_pht"], y=span["demand_mw"], name="Demand", line=dict(color=theme.INK, width=2.5, shape="hv"))
drill.add_scatter(x=span["timestamp_pht"], y=span["combined_mw"], name="Solar + wind", line=dict(color=theme.LEAF, width=2.5),
                  fill="tozeroy", fillcolor="rgba(110,231,183,.12)")
drill.add_scatter(x=span["timestamp_pht"], y=span["battery_soc_end_mwh"], name="Battery (MWh)",
                  line=dict(color=theme.VIOLET, width=2.5, dash="dot"))
theme.chart(theme.style(drill, "", "MW · MWh", 340), key="drill")

with st.expander("Hourly results table and download"):
    cols = ["timestamp_pht", "solar_mw", "wind_mw", "combined_mw", "demand_mw", "battery_soc_end_mwh",
            "grid_import_mwh", "curtailed_renewable_mwh"]
    shown = full.loc[full["timestamp_pht"].dt.date == outage_day, cols]
    st.dataframe(shown, hide_index=True, width="stretch")
    st.download_button(
        "Download every hour, 2020 to June 2026, for this design (CSV)",
        dispatch_csv(site, cfg["load_scale"], cfg["battery_capacity"], **physics_args(cfg)),
        file_name=f"habagat_{SITE_SHORT[site].lower().replace(' ', '_')}_2020_2026.csv",
        mime="text/csv",
        icon=":material/download:",
    )
