import datetime as dt

import plotly.graph_objects as go
import streamlit as st

from solwind import scenes, theme, ui
from solwind.daypicker import day_picker
from solwind.data import SITE_SHORT, current_dispatch, settings

theme.header('Live plant', 'One simulated day, hour by hour.')

cfg = settings()
top = st.columns([1.3, 2.4], vertical_alignment="bottom")
with top[0]:
    site = ui.site_picker()
dispatch = current_dispatch(site)
day_pick = day_picker("plant_date", site, dt.date(2022, 9, 15), key="plant_picker")

day = dispatch.loc[dispatch["timestamp_pht"].dt.date == day_pick].reset_index(drop=True)
label = f"{SITE_SHORT[site]} · {day_pick:%a %d %b %Y}"
scenes.plant(day, cfg, label)

share = 100 * (day["renewable_to_load_mwh"].sum() + day["battery_discharge_to_load_mwh"].sum()) / day["demand_mw"].sum()
m = st.columns(5)
m[0].metric("Generated", f"{day['combined_mw'].sum():.2f} MWh")
m[1].metric("Renewable share", f"{share:.0f}%")
m[2].metric("Bought from grid", f"{day['grid_import_mwh'].sum():.2f} MWh")
m[3].metric("Unused renewables", f"{day['curtailed_renewable_mwh'].sum():.2f} MWh")
m[4].metric("Peak hub wind", f"{day['hub_wind_m_s'].max():.1f} m/s")

fig = go.Figure()
fig.add_scatter(x=day["timestamp_pht"], y=day["solar_mw"], name="Solar", stackgroup="g",
                line=dict(color=theme.SUN, width=0), fillcolor="rgba(232,163,23,.85)")
fig.add_scatter(x=day["timestamp_pht"], y=day["wind_mw"], name="Wind", stackgroup="g",
                line=dict(color=theme.SEA, width=0), fillcolor="rgba(47,111,222,.6)")
fig.add_scatter(x=day["timestamp_pht"], y=day["demand_mw"], name="Demand", line=dict(color=theme.INK, width=2.5, shape="hv"))
fig.add_scatter(x=day["timestamp_pht"], y=day["battery_soc_end_mwh"], name="Battery (MWh)", yaxis="y2",
                line=dict(color=theme.VIOLET, width=2.5, dash="dot"))
fig.update_layout(
    yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Battery MWh", rangemode="tozero",
                tickfont=dict(family=theme.FONT_MONO, size=11, color=theme.VIOLET)),
)
fig.update_yaxes(rangemode="tozero")
theme.chart(theme.style(fig, "The same day as a ledger", "MW"), key="plant_day")
theme.note(
    f"{cfg['solar_capacity']:g} MW solar · {cfg['wind_capacity']:g} MW wind · {cfg['battery_capacity']:g} MWh battery · "
    f"demand ×{cfg['load_scale']:g}"
)
