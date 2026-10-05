import datetime as dt

import plotly.graph_objects as go
import streamlit as st

from habagat import scenes, theme, ui
from habagat.daypicker import day_picker
from habagat.data import MODEL_LABEL, MODELS, SITE_SHORT, SITES, headline_findings, load_plan_summary, load_replay

theme.header('Grid planning', "Each forecast sets an hourly grid-purchase plan at midnight. The day is then replayed with actual generation. Adjustment is the extra energy bought plus planned energy that wasn't needed.")

summary = load_plan_summary()
found = headline_findings()
fig = go.Figure()
for field, name, color in [("extra_grid_mwh", "Extra energy needed", theme.EMBER),
                           ("unused_grid_plan_mwh", "Planned but unused", theme.SUN)]:
    for i, model in enumerate(MODELS):
        rows = summary.loc[summary["model"] == model].set_index("location").reindex(SITES)
        fig.add_bar(
            y=[[SITE_SHORT[s] for s in SITES], [MODEL_LABEL[model]] * 3], x=rows[field], name=name,
            orientation="h", marker_color=color, marker_line_color=theme.INK,
            marker_line_width=1.4 if model == "xgboost" else 0, legendgroup=field, showlegend=i == 0,
        )
fig.update_layout(barmode="stack", bargap=.25, hovermode="y unified")
fig.update_yaxes(autorange="reversed", ticks="", tickfont=dict(family=theme.FONT_MONO, size=11))
fig.update_xaxes(title="MWh over 2025 (8,760 hours)")
lead, side = st.columns([2, 1], gap="large")
with lead:
    theme.chart(theme.style(fig, "Total grid-plan adjustment in 2025", "", 470), key="plan_summary")
with side:
    for site in SITES:
        st.metric(f"{SITE_SHORT[site]} · XGBoost",
                  f"{summary.set_index(['location', 'model']).loc[(site, 'xgboost'), 'total_grid_adjustment_mwh']:.0f} MWh",
                  f"{-found['plan_cut'].loc[site]:.1f}% vs best baseline", delta_color="inverse")
    theme.note("<b>Same outcome, different plans.</b> Battery dispatch and load served are identical for every "
               "method. Only the plan, and how far it had to be corrected, changes.")

theme.section('Day replay', 'The dashed forecast is fixed at 00:00. Actual generation is revealed as the playhead moves.')
replay = load_replay()
c = st.columns(2, vertical_alignment="bottom")
with c[0]:
    site = ui.site_picker()
with c[1]:
    model = ui.model_picker("plan_model")
day = day_picker("plan_date", site, dt.date(2025, 7, 15), key="plan_picker",
                 first=dt.date(2025, 1, 1), last=dt.date(2025, 12, 31))
sel = replay.loc[(replay["location"] == site) & (replay["timestamp"].dt.date == day)].sort_values("timestamp")
scenes.replay(sel, model, MODEL_LABEL[model], f"{SITE_SHORT[site]} · {day:%d %b %Y}")

totals = {m: float((sel[f"{m}_extra_grid_mwh"] + sel[f"{m}_unused_grid_plan_mwh"]).sum()) for m in MODELS}
k = st.columns(3)
for col, m in zip(k, MODELS):
    best = min(totals, key=totals.get) == m
    col.metric(f"{MODEL_LABEL[m]} · adjustment this day", f"{totals[m]:.3f} MWh", "best this day" if best else None,
               delta_color="normal" if best else "off")
st.caption("A retrospective planning scenario, not a live market result. Real-time grid adjustment is assumed available. "
           "The battery starts at 1 MWh on 1 January and carries its charge through the year.")
