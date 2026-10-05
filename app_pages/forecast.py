import datetime as dt

import plotly.graph_objects as go
import streamlit as st

from habagat import theme, ui
from habagat.daypicker import day_picker
from habagat.data import MODEL_LABEL, MODELS, SITE_SHORT, SITES, headline_findings, load_metrics, load_predictions

theme.header('Forecast accuracy', 'Day-ahead forecasts issued at 00:00 for every day of 2025, a year held out from training. Error is measured against the reference modeled output.')

metrics = load_metrics()
overall = metrics.loc[(metrics["scope"] == "all_hours") & (metrics["aggregation"] == "overall")]
found = headline_findings()

board = go.Figure()
combined = overall.loc[overall["source"] == "combined"].set_index(["location", "model"])["mae_mw"]
for model in MODELS:
    board.add_bar(
        x=[SITE_SHORT[s] for s in SITES], y=[combined.loc[(s, model)] for s in SITES], name=MODEL_LABEL[model],
        marker_color=theme.MODEL_COLOR[model], text=[f"{combined.loc[(s, model)]:.3f}" for s in SITES],
        textposition="outside", textfont=dict(family=theme.FONT_MONO, size=11),
    )
board.update_layout(barmode="group", bargap=.3, bargroupgap=.08, hovermode="x unified")
lead, side = st.columns([2, 1], gap="large")
with lead:
    theme.chart(theme.style(board, "Leaderboard · combined solar + wind error (MAE, lower is better)", "MW", 360), key="board")
with side:
    for site in SITES:
        st.metric(
            f"{SITE_SHORT[site]} · XGBoost MAE",
            f"{combined.loc[(site, 'xgboost')]:.3f} MW",
            f"{-found['mae_cut'].loc[site]:.1f}% vs best baseline",
            delta_color="inverse",
        )

st.divider()
c = st.columns([1.3, .8, 1.5], vertical_alignment="bottom")
with c[0]:
    site = ui.site_picker()
with c[1]:
    st.session_state.setdefault("fc_source", "combined")
    source = st.segmented_control("Source", ["combined", "solar", "wind"], key="fc_source",
                                  format_func=str.title, width="stretch") or "combined"

by_horizon = metrics.loc[(metrics["scope"] == "all_hours") & (metrics["aggregation"] == "horizon")
                         & (metrics["location"] == site) & (metrics["source"] == source)]
by_month = metrics.loc[(metrics["scope"] == "all_hours") & (metrics["aggregation"] == "month")
                       & (metrics["location"] == site) & (metrics["source"] == source)]
h_fig, m_fig = go.Figure(), go.Figure()
for model in MODELS:
    style = dict(color=theme.MODEL_COLOR[model], width=3 if model == "xgboost" else 2)
    hz = by_horizon.loc[by_horizon["model"] == model].sort_values("horizon_hour")
    mo = by_month.loc[by_month["model"] == model].sort_values("target_month")
    h_fig.add_scatter(x=hz["horizon_hour"], y=hz["mae_mw"], name=MODEL_LABEL[model], line=style, mode="lines")
    m_fig.add_scatter(x=theme.MONTHS, y=mo["mae_mw"], name=MODEL_LABEL[model], line=style, mode="lines+markers")
h_fig.update_xaxes(title="Hours ahead (issued 00:00)", dtick=3)
m_fig.update_xaxes(type="category")
a, b = st.columns(2)
with a:
    theme.chart(theme.style(h_fig, f"{SITE_SHORT[site]} · error by hour ahead", "MAE · MW", 330), key="horizon")
with b:
    theme.chart(theme.style(m_fig, f"{SITE_SHORT[site]} · error by month", "MAE · MW", 330), key="month")

theme.section('Single-day playback', 'Hide the reference to compare the forecast alone first.')
predictions = load_predictions()
day = day_picker("fc_date", site, dt.date(2025, 7, 15), key="fc_picker",
                 first=dt.date(2025, 1, 1), last=dt.date(2025, 12, 31))
p = st.columns([1.4, 1, 1], vertical_alignment="bottom")
with p[0]:
    model = ui.model_picker("fc_model")
with p[1]:
    reveal = st.toggle("Reveal the reference", value=True)
with p[2]:
    everyone = st.toggle("Show all three methods", value=False)

sel = predictions.loc[(predictions["location"] == site) & (predictions["target_timestamp_pht"].dt.date == day)]
if source == "combined":
    sel = sel.groupby("target_timestamp_pht", as_index=False).sum(numeric_only=True)
else:
    sel = sel.loc[sel["source"] == source]
sel = sel.sort_values("target_timestamp_pht").reset_index(drop=True)

shown = MODELS if everyone else [model]
fig = go.Figure()
fig.add_scatter(x=sel["target_timestamp_pht"], y=sel["reference_output_mw"], name="Reference (what happened)",
                line=dict(color=theme.INK, width=3), fill="tozeroy", fillcolor="rgba(234,242,246,.06)",
                visible=True if reveal else "legendonly")
for m in shown:
    fig.add_scatter(x=sel["target_timestamp_pht"], y=sel[f"{m}_prediction_mw"], name=MODEL_LABEL[m],
                    line=dict(color=theme.MODEL_COLOR[m], width=2.6, dash="dash"))
fig.frames = [
    go.Frame(
        data=[go.Scatter(x=sel["target_timestamp_pht"][:n], y=sel["reference_output_mw"][:n])]
        + [go.Scatter(x=sel["target_timestamp_pht"][:n], y=sel[f"{m}_prediction_mw"][:n]) for m in shown],
        name=str(n),
    )
    for n in range(1, len(sel) + 1)
]
button = dict(font=dict(family=theme.FONT_MONO, size=11, color=theme.INK), bgcolor=theme.PAPER, bordercolor=theme.INK)
fig.update_layout(
    updatemenus=[dict(
        type="buttons", direction="left", x=0, y=-0.13, xanchor="left", yanchor="top", showactive=False, pad=dict(r=6), **button,
        buttons=[
            dict(label="▶ Play day", method="animate",
                 args=[None, {"frame": {"duration": 170, "redraw": False}, "transition": {"duration": 120}, "fromcurrent": False}]),
            dict(label="Pause", method="animate", args=[[None], {"frame": {"duration": 0}, "mode": "immediate"}]),
        ],
    )],
)
fig.update_yaxes(range=[0, max(sel[["reference_output_mw"] + [f"{m}_prediction_mw" for m in MODELS]].max().max() * 1.15, 0.05)])
fig.update_xaxes(range=[sel["target_timestamp_pht"].min(), sel["target_timestamp_pht"].max()])
fig.update_layout(margin=dict(b=70))
theme.chart(theme.style(fig, f"{source.title()} output · {SITE_SHORT[site]} · {day:%d %b %Y}", "MW", 420), key="playback")

err = (sel[f"{model}_prediction_mw"] - sel["reference_output_mw"]).abs()
q = st.columns(3)
q[0].metric(f"{MODEL_LABEL[model]} error this day", f"{err.mean():.3f} MW")
q[1].metric("Worst hour", f"{sel.loc[err.idxmax(), 'target_timestamp_pht']:%H:00}", f"{err.max():.3f} MW off", delta_color="off")
q[2].metric("Energy forecast vs reference", f"{sel[f'{model}_prediction_mw'].sum():.2f} MWh",
            f"{sel[f'{model}_prediction_mw'].sum() - sel['reference_output_mw'].sum():+.2f} MWh", delta_color="off")
theme.note(
    "<b>Reference</b> is electricity calculated from the 2025 weather with the same physics. It is not metered plant output. "
    "Models were trained on 2020–2023, selected on 2024 and scored once on 2025. The Rolling test page repeats this for 2024 and January–June 2026."
)
