import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from habagat import theme
from habagat.data import SITE_ISLAND, SITE_SHORT, SITES, current_generation, load_weather, settings

theme.header('Compare sites', 'The same equipment at Laoag, Mactan and General Santos, 2020–2024.')

cfg = settings()
generation = current_generation()
years = generation["timestamp_pht"].dt.year.nunique()
annual = generation.groupby("location")[["solar_mw", "wind_mw"]].sum().div(years).reindex(SITES)

left, right = st.columns(2, gap="medium")
with left:
    mix = go.Figure()
    labels = [SITE_SHORT[s] for s in SITES]
    mix.add_bar(y=labels, x=annual["solar_mw"], name="Solar", orientation="h", marker_color=theme.SUN)
    mix.add_bar(y=labels, x=annual["wind_mw"], name="Wind", orientation="h", marker_color=theme.SEA)
    mix.update_layout(barmode="stack", bargap=.45, hovermode="y unified")
    mix.update_yaxes(autorange="reversed", ticks="")
    theme.chart(theme.style(mix, "Average energy per year (MWh)", "", 300), key="mix")

with right:
    monthly = generation.assign(month=generation["timestamp_pht"].dt.month).groupby(["location", "month"])["combined_mw"].mean()
    trend = go.Figure()
    for s in SITES:
        trend.add_scatter(x=theme.MONTHS, y=monthly.loc[s], name=SITE_SHORT[s], mode="lines+markers",
                          line=dict(color=theme.SITE_COLOR[s], width=2.6, shape="spline"), marker=dict(size=6))
    trend.update_xaxes(type="category")
    theme.chart(theme.style(trend, "Average combined output by month", "MW", 300), key="monthly")

theme.section('Wind direction and speed', 'Share of hours by direction at hub height (69 m), 2020–2024.')
weather_all = load_weather()
bins = [0, 3, 6, 9, 12, 40]
bin_names = ["<3 m/s", "3–6", "6–9", "9–12", "12+"]
shades = ["#22343D", "#2C5A6E", "#3C88AA", "#5BB5E0", "#C3E7F7"]
roses = make_subplots(rows=1, cols=3, specs=[[{"type": "polar"}] * 3],
                      subplot_titles=[f"{SITE_SHORT[s]} · {SITE_ISLAND[s]}" for s in SITES])
for i, site in enumerate(SITES, start=1):
    w = weather_all.loc[weather_all["location"] == site]
    hub = generation.loc[generation["location"] == site, "hub_wind_m_s"].to_numpy()
    sector = ((w["wind_direction_50m_deg"].to_numpy() + 11.25) // 22.5).astype(int) % 16
    speed = pd.cut(hub, bins, labels=bin_names, right=False)
    table = pd.crosstab(sector, speed, normalize=True).reindex(range(16), fill_value=0) * 100
    for name, shade in zip(bin_names, shades):
        roses.add_barpolar(
            r=table.get(name, pd.Series(0, index=range(16))), theta=np.arange(16) * 22.5, name=name,
            marker_color=shade, marker_line_color=theme.PAPER, marker_line_width=.6,
            showlegend=i == 1, row=1, col=i, hovertemplate="%{theta}° · %{r:.1f}% of hours<extra>" + name + "</extra>",
        )
polar = dict(
    bgcolor="rgba(0,0,0,0)",
    angularaxis=dict(direction="clockwise", rotation=90, tickvals=[0, 90, 180, 270], ticktext=["N", "E", "S", "W"],
                     tickfont=dict(family=theme.FONT_MONO, size=11), linecolor="#3A4249", gridcolor="#2B3137"),
    radialaxis=dict(showticklabels=False, gridcolor="#2B3137", linecolor="rgba(0,0,0,0)"),
)
roses.update_layout(polar=polar, polar2=polar, polar3=polar, height=400, hovermode="closest",
                    margin=dict(l=30, r=30, t=60, b=10), legend=dict(y=-0.05, yanchor="top", x=.5, xanchor="center"))
roses.update_annotations(font=dict(family=theme.FONT_HEAD, size=16, color=theme.INK), yshift=14)
theme.chart(roses, key="roses")

theme.section('Solar–wind complementarity', "Negative correlation means one source tends to produce when the other doesn't.")
rows = []
for site in SITES:
    g = generation.loc[generation["location"] == site]
    cap = cfg["solar_capacity"] + cfg["wind_capacity"]
    solar_low = g["solar_mw"] < 0.1 * max(cfg["solar_capacity"], 1e-9)
    rows.append({
        "Site": SITE_SHORT[site],
        "Solar–wind correlation": g["solar_mw"].corr(g["wind_mw"]),
        "Capacity factor": 100 * g["combined_mw"].mean() / cap if cap else 0.0,
        "Hours below 10% output": 100 * (g["combined_mw"] < 0.1 * cap).mean() if cap else 100.0,
        "Wind helps when sun is low": 100 * (g.loc[solar_low, "wind_mw"] >= 0.1 * max(cfg["wind_capacity"], 1e-9)).mean(),
    })
st.dataframe(
    pd.DataFrame(rows),
    hide_index=True,
    width="stretch",
    column_config={
        "Solar–wind correlation": st.column_config.NumberColumn(format="%.3f"),
        "Capacity factor": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=40),
        "Hours below 10% output": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
        "Wind helps when sun is low": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
    },
)
