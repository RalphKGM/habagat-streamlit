import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from habagat import theme
from habagat.data import SITE_ISLAND, SITE_SHORT, SITES, current_generation, load_weather, settings

theme.header(
    "Sites",
    "North, centre, south: <em>who gets the wind?</em>",
    "The same equipment on three coasts. Laoag catches the northeast Amihan monsoon. General Santos sits below "
    "the typhoon belt with steady sun and little wind. Mactan falls in between.",
)

cfg = settings()
generation = current_generation()
years = generation["timestamp_pht"].dt.year.nunique()
weather = load_weather().drop_duplicates("location").set_index("location")
annual = generation.groupby("location")[["solar_mw", "wind_mw"]].sum().div(years).reindex(SITES)

left, right = st.columns([1, 1.25], gap="large")
with left:
    geo = go.Figure()
    geo.add_scattergeo(
        lat=weather.loc[SITES, "latitude_deg"],
        lon=weather.loc[SITES, "longitude_deg"],
        text=[f"<b>{SITE_SHORT[s]}</b><br>{annual.loc[s].sum():,.0f} MWh/yr" for s in SITES],
        hoverinfo="text",
        mode="markers+text",
        textposition=["middle left", "middle right", "middle left"],
        textfont=dict(family=theme.FONT_MONO, size=12, color=theme.INK),
        marker=dict(
            size=[14 + annual.loc[s].sum() / 120 for s in SITES],
            color=[theme.SITE_COLOR[s] for s in SITES],
            line=dict(color=theme.INK, width=1.5),
            opacity=.9,
        ),
    )
    geo.update_geos(
        projection_type="mercator",
        lataxis_range=[4.2, 21.3],
        lonaxis_range=[115.5, 128.5],
        showland=True, landcolor="#E3D6BB",
        showocean=True, oceancolor="#C9DCE0",
        showcountries=False, showcoastlines=True, coastlinecolor=theme.INK, coastlinewidth=.8,
        showframe=False, resolution=50, bgcolor="rgba(0,0,0,0)",
    )
    geo.update_layout(height=520, margin=dict(l=0, r=0, t=10, b=0), hovermode="closest")
    theme.chart(geo, key="map")

with right:
    mix = go.Figure()
    labels = [SITE_SHORT[s] for s in SITES]
    mix.add_bar(y=labels, x=annual["solar_mw"], name="Solar", orientation="h", marker_color=theme.SUN)
    mix.add_bar(y=labels, x=annual["wind_mw"], name="Wind", orientation="h", marker_color=theme.SEA)
    mix.update_layout(barmode="stack", bargap=.45, hovermode="y unified")
    mix.update_yaxes(autorange="reversed", ticks="")
    theme.chart(theme.style(mix, "Average annual energy", "", 250), key="mix")

    monthly = generation.assign(month=generation["timestamp_pht"].dt.month).groupby(["location", "month"])["combined_mw"].mean()
    trend = go.Figure()
    for s in SITES:
        trend.add_scatter(x=theme.MONTHS, y=monthly.loc[s], name=SITE_SHORT[s], mode="lines+markers",
                          line=dict(color=theme.SITE_COLOR[s], width=2.6, shape="spline"), marker=dict(size=6))
    trend.update_xaxes(type="category")
    theme.chart(theme.style(trend, "Average combined output by month", "MW", 270), key="monthly")

theme.header(
    "Wind roses",
    "Where the wind <em>comes from</em>",
    "Frequency of hub-height wind by direction (50 m data sheared to the 69 m hub), 2020–2024. "
    "Darker petals are faster winds.",
)
weather_all = load_weather()
bins = [0, 3, 6, 9, 12, 40]
bin_names = ["<3 m/s", "3–6", "6–9", "9–12", "12+"]
shades = ["#D7E4E8", "#9EC0CB", "#5D93AB", "#2D6A8A", "#16232A"]
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
                     tickfont=dict(family=theme.FONT_MONO, size=11), linecolor=theme.INK, gridcolor="rgba(22,35,42,.12)"),
    radialaxis=dict(showticklabels=False, gridcolor="rgba(22,35,42,.12)", linecolor="rgba(0,0,0,0)"),
)
roses.update_layout(polar=polar, polar2=polar, polar3=polar, height=400, hovermode="closest",
                    margin=dict(l=30, r=30, t=60, b=10), legend=dict(y=-0.05, yanchor="top", x=.5, xanchor="center"))
roses.update_annotations(font=dict(family=theme.FONT_HEAD, size=16, color=theme.INK), yshift=14)
theme.chart(roses, key="roses")

theme.header(
    "Complementarity",
    "Does the wind <em>cover for the sun?</em>",
    "A hybrid plant helps most when one source fills the other’s gaps. Negative correlation is good here.",
)
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
