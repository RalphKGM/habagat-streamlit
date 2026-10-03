import datetime as dt

import plotly.graph_objects as go
import streamlit as st

from habagat import scenes, theme, ui
from habagat.data import SITE_SHORT, current_dispatch, settings

theme.header(
    "Live plant",
    "Watch one day <em>unfold</em>, hour by hour",
    "The sun follows the real hour. The rotor turns with simulated wind output and the clouds follow NASA POWER "
    "cloud cover. Energy moves along the lines in proportion to megawatts. Everything is computed from the "
    "weather for the day you pick.",
)

cfg = settings()
top = st.columns([1.3, 1, 1.4], vertical_alignment="bottom")
with top[0]:
    site = ui.site_picker()
dispatch = current_dispatch(site)
daily = (
    dispatch.assign(date=dispatch["timestamp_pht"].dt.date)
    .groupby("date")
    .agg(solar=("solar_mw", "sum"), wind=("wind_mw", "sum"), grid=("grid_import_mwh", "sum"))
)
presets = {
    "Windiest": daily["wind"].idxmax(),
    "Sunniest": daily["solar"].idxmax(),
    "Hardest day": daily["grid"].idxmax(),
}
st.session_state.setdefault("plant_date", dt.date(2022, 9, 15))


def _jump(day: dt.date) -> None:
    st.session_state.plant_date = day


with top[1]:
    day_pick = st.date_input(
        "Day", key="plant_date", min_value=daily.index.min(), max_value=daily.index.max(), format="YYYY-MM-DD"
    )
with top[2]:
    st.caption(f"Notable days at {SITE_SHORT[site]}")
    cols = st.columns(len(presets))
    for col, (name, day) in zip(cols, presets.items()):
        col.button(name, on_click=_jump, args=(day,), width="stretch", help=f"{day:%d %b %Y}")

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
                line=dict(color=theme.SUN, width=0), fillcolor="rgba(229,154,43,.75)")
fig.add_scatter(x=day["timestamp_pht"], y=day["wind_mw"], name="Wind", stackgroup="g",
                line=dict(color=theme.SEA, width=0), fillcolor="rgba(45,106,138,.7)")
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
    "<b>System:</b> "
    f"{cfg['solar_capacity']:g} MW solar · {cfg['wind_capacity']:g} MW wind · {cfg['battery_capacity']:g} MWh battery · "
    f"demand ×{cfg['load_scale']:g}. Change these in the System designer. Demand is the study’s standardized "
    "scenario, not measured city load."
)
