import datetime as dt

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from habagat import theme, ui
from habagat.data import (
    FOLD_LABEL, FOLD_WINDOWS, FOLDS, MODEL_LABEL, MODELS, SITE_SHORT, SITES,
    load_rolling_bootstrap, load_rolling_hourly, load_rolling_metrics, load_rolling_plan, rolling_daily,
)

theme.header(
    "Rolling test",
    "The same forecast, re-run as if it were 2024, 2025 and 2026. Each year is predicted by a model that only saw the "
    "years before it. 2026 stops at June, the last month with complete NASA solar data.",
)

# --- How the window moves -----------------------------------------------------------------------
YEARS = list(range(2020, 2027))
ROLE = {"fit": ("Fit", theme.STONE), "select": ("Select", theme.VIOLET), "test": ("Test", theme.HI), "": ("", theme.SURFACE)}


def _role(fold: str, year: int) -> str:
    (f0, f1), select, (r0, r1), test = FOLD_WINDOWS[fold]
    if year == test:
        return "test"
    if year == select:
        return "select"
    if f0 <= year <= f1:
        return "fit"
    return ""


cells = "".join(f'<div class="rt-y">{y}</div>' for y in YEARS)
for fold in FOLDS:
    cells += f'<div class="rt-name">{FOLD_LABEL[fold]}</div>'
    for y in YEARS:
        role = _role(fold, y)
        label, color = ROLE[role]
        text = "Jan–Jun" if role == "test" and y == 2026 else label
        cells += f'<div class="rt-c rt-{role or "none"}" style="--c:{color}">{text}</div>'
theme.html(
    f"""<style>
    .rt-grid {{ display:grid; grid-template-columns: 210px repeat({len(YEARS)}, 1fr); gap:3px; margin:.4rem 0 .2rem; }}
    .rt-grid > div {{ font-family:{theme.FONT_MONO}; font-size:.72rem; padding:.42rem .5rem; }}
    .rt-y {{ color:{theme.INK_SOFT}; text-align:center; }}
    .rt-y:first-child {{ grid-column:2; }}
    .rt-name {{ color:{theme.INK}; font-family:{theme.FONT_HEAD} !important; font-size:.92rem !important; letter-spacing:.04em;
                text-transform:uppercase; border-left:2px solid {theme.RULE}; }}
    .rt-c {{ text-align:center; color:{theme.PAPER}; background:var(--c); font-weight:500; }}
    .rt-none {{ background:transparent; border:1px dashed {theme.RULE}; color:transparent; }}
    .rt-fit {{ color:{theme.INK}; }}
    .rt-key {{ font-size:.82rem; color:{theme.INK_SOFT}; margin:.1rem 0 1rem; }}
    @media (max-width: 720px) {{ .rt-grid {{ grid-template-columns: 110px repeat({len(YEARS)}, 1fr); }}
                                 .rt-grid > div {{ font-size:.6rem; padding:.3rem .1rem; }} }}
    </style>
    <div class="rt-grid"><div></div>{cells}</div>
    <div class="rt-key">Fit: the two candidate settings learn. Select: the better setting is chosen on the next year.
    The chosen setting is then refit on every year before the test year. The test year is scored once.</div>"""
)

# --- Results across folds -----------------------------------------------------------------------
metrics = load_rolling_metrics()
overall = metrics.loc[
    (metrics["period"] == "available_test") & (metrics["scope"] == "all_hours")
    & (metrics["aggregation"] == "overall") & (metrics["source"] == "combined")
].set_index(["fold", "location", "model"])["mae_mw"]
plan = load_rolling_plan().set_index(["fold", "location", "model"])

main_folds = ["rolling_2024", "rolling_2025", "rolling_2026"]
theme.html(
    '<div class="rt-key" style="margin:.2rem 0 .1rem">Combined solar + wind error in each test year · '
    + " · ".join(f'<span style="color:{theme.MODEL_COLOR[m]}">■ {MODEL_LABEL[m]}</span>' for m in MODELS)
    + "</div>"
)
cols = st.columns(3, gap="medium")
for col, site in zip(cols, SITES):
    fig = go.Figure()
    for model in MODELS:
        fig.add_scatter(
            x=[FOLD_LABEL[f] for f in main_folds], y=[overall.loc[(f, site, model)] for f in main_folds],
            name=MODEL_LABEL[model], mode="lines+markers",
            line=dict(color=theme.MODEL_COLOR[model], width=3 if model == "xgboost" else 1.8),
            marker=dict(size=9 if model == "xgboost" else 6, symbol="square"),
        )
    fig.update_xaxes(type="category")
    fig.update_yaxes(rangemode="tozero")
    fig.update_layout(showlegend=False)
    with col:
        theme.chart(theme.style(fig, f"{SITE_SHORT[site]} · combined MAE", "MW", 300), key=f"fold_{site}")
        cut = [1 - overall.loc[(f, site, "xgboost")] / min(overall.loc[(f, site, "previous_day")],
                                                           overall.loc[(f, site, "training_climatology")])
               for f in main_folds]
        st.metric("XGBoost vs best baseline, each year", f"−{min(cut) * 100:.0f}% to −{max(cut) * 100:.0f}%")

theme.note(
    "XGBoost has the lowest combined error and the smallest grid-plan adjustment at every site in every test. "
    "That is the point of the rolling test: the result repeats across years instead of depending on one lucky year."
)

# --- Year at a glance ---------------------------------------------------------------------------
theme.section(
    "Every day, not one at a time",
    "The model forecasts all days automatically at midnight. Each square is one day: green means XGBoost beat "
    "yesterday's-output forecast that day, red means it lost. Click a square to open it.",
)
c = st.columns([1.3, 1.6], vertical_alignment="bottom")
with c[0]:
    site = ui.site_picker()
with c[1]:
    st.session_state.setdefault("roll_fold", "rolling_2025")
    fold = st.segmented_control("Test", FOLDS, key="roll_fold", format_func=FOLD_LABEL.get, width="stretch") or "rolling_2025"

daily = rolling_daily()
days = daily.loc[(daily["fold"] == fold) & (daily["location"] == site)].copy()
days["gain"] = days["previous_day_mae"] - days["xgboost_mae"]
stamp = pd.to_datetime(days["day"])
days["week"] = (stamp - pd.to_timedelta(stamp.dt.weekday, unit="D")).dt.date
days["weekday"] = stamp.dt.weekday
won = (days["gain"] > 0).mean()

limit = float(days["gain"].abs().quantile(0.95)) or 0.05
cal = go.Figure(go.Scatter(
    x=days["week"], y=days["weekday"], mode="markers",
    marker=dict(symbol="square", size=12, color=days["gain"], colorscale=theme.DIVERGING, cmin=-limit, cmax=limit,
                line=dict(width=0),
                colorbar=dict(title=dict(text="MW better", side="right"), thickness=8, len=.9, tickfont=dict(size=10))),
    customdata=pd.DataFrame({"d": days["day"].astype(str), "x": days["xgboost_mae"], "p": days["previous_day_mae"]}),
    hovertemplate="%{customdata[0]}<br>XGBoost %{customdata[1]:.3f} MW · previous day %{customdata[2]:.3f} MW<extra></extra>",
))
cal.update_yaxes(tickvals=list(range(7)), ticktext=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                 autorange="reversed", showgrid=False, zeroline=False)
cal.update_xaxes(showgrid=False, dtick="M1", tickformat="%b")
cal.update_layout(dragmode=False, clickmode="event+select", margin=dict(t=46, b=30))
event = st.plotly_chart(
    theme.style(cal, f"{SITE_SHORT[site]} · {FOLD_LABEL[fold]} · XGBoost won {won:.0%} of {len(days)} days", "", 250),
    key=f"cal_{fold}_{site}", on_select="rerun", selection_mode="points", config={"displayModeBar": False}, theme=None,
)

points = (event or {}).get("selection", {}).get("points", []) if event else []
first, last = days["day"].min(), days["day"].max()
if points:
    st.session_state.roll_day = dt.date.fromisoformat(points[0]["customdata"][0])
fallback = dt.date(first.year, 7, 15) if last.month > 7 else dt.date(first.year, 3, 15)
picked = st.session_state.get("roll_day", fallback)
if not first <= picked <= last:
    picked = fallback

hourly = load_rolling_hourly()
sel = hourly.loc[(hourly["fold"] == fold) & (hourly["location"] == site)
                 & (hourly["target_timestamp_pht"].dt.date == picked)].sort_values("target_timestamp_pht")
row = days.loc[days["day"] == picked].iloc[0]

a, b = st.columns([2.2, 1], gap="large")
with a:
    fig = go.Figure()
    fig.add_scatter(x=sel["target_timestamp_pht"], y=sel["reference_output_mw"], name="Reference (what happened)",
                    line=dict(color=theme.INK, width=3), fill="tozeroy", fillcolor="rgba(234,242,246,.06)")
    for model in MODELS:
        fig.add_scatter(x=sel["target_timestamp_pht"], y=sel[f"{model}_prediction_mw"], name=MODEL_LABEL[model],
                        line=dict(color=theme.MODEL_COLOR[model], width=2.6 if model == "xgboost" else 1.8, dash="dash"))
    fig.update_xaxes(tickformat="%H:00")
    theme.chart(theme.style(fig, f"{picked:%a %d %b %Y} · combined solar + wind, issued at 00:00", "MW", 340), key="roll_day_chart")
with b:
    st.metric("XGBoost error this day", f"{row['xgboost_mae']:.3f} MW",
              f"{row['xgboost_mae'] - row['previous_day_mae']:+.3f} vs previous day", delta_color="inverse")
    st.metric("Grid-plan adjustment", f"{row['xgboost_adjust']:.2f} MWh",
              f"{row['xgboost_adjust'] - row['previous_day_adjust']:+.2f} vs previous day", delta_color="inverse")
    st.metric("Energy that day", f"{row['reference_mwh']:.2f} MWh", "modeled reference", delta_color="off")

# --- Uncertainty and planning ---------------------------------------------------------------------
theme.section(
    "Is the gap real?",
    "Paired block bootstrap: the same days are resampled in seven-day blocks 2,000 times. Bars left of zero favour "
    "XGBoost. Every interval stays left of zero.",
)
boot = load_rolling_bootstrap()
boot = boot.loc[(boot["fold"] == fold) & (boot["period"] == "available_test")]
forest = go.Figure()
for i, baseline in enumerate(["previous_day", "training_climatology"]):
    part = boot.loc[boot["baseline"] == baseline].set_index("location").reindex(SITES)
    forest.add_scatter(
        x=part["delta_mae_mw"], y=[k + (0.14 if i == 0 else -0.14) for k in range(len(SITES))],
        name=f"vs {MODEL_LABEL[baseline]}", mode="markers",
        marker=dict(color=theme.MODEL_COLOR[baseline], size=11, symbol="square"),
        error_x=dict(type="data", symmetric=False, array=part["ci95_upper_mw"] - part["delta_mae_mw"],
                     arrayminus=part["delta_mae_mw"] - part["ci95_lower_mw"], thickness=2, width=0,
                     color=theme.MODEL_COLOR[baseline]),
        customdata=part[["ci95_lower_mw", "ci95_upper_mw"]].to_numpy(),
        hovertemplate="%{x:.4f} MW (95%: %{customdata[0]:.4f} to %{customdata[1]:.4f})<extra>%{fullData.name}</extra>",
    )
forest.update_yaxes(tickvals=list(range(len(SITES))), ticktext=[SITE_SHORT[s] for s in SITES], range=[len(SITES) - .4, -.6],
                    showgrid=False)
forest.add_vline(x=0, line=dict(color=theme.INK_SOFT, width=1, dash="dot"))
forest.update_layout(legend=dict(orientation="h", x=0, xanchor="left", y=1.0, yanchor="bottom"), margin=dict(t=80))
forest.update_xaxes(title="XGBoost minus baseline, daily MAE (MW) · 95% interval")

adj = go.Figure()
for model in MODELS:
    vals = [plan.loc[(fold, s, model), "mean_hourly_grid_adjustment_mwh"] for s in SITES]
    adj.add_bar(x=[SITE_SHORT[s] for s in SITES], y=vals, name=MODEL_LABEL[model], marker_color=theme.MODEL_COLOR[model],
                text=[f"{v:.3f}" for v in vals], textposition="outside", textfont=dict(family=theme.FONT_MONO, size=10))
adj.update_layout(barmode="group", bargap=.3, legend=dict(orientation="h", x=0, xanchor="left", y=1.0, yanchor="bottom"), margin=dict(t=80))
adj.update_yaxes(rangemode="tozero", range=[0, plan.loc[fold, "mean_hourly_grid_adjustment_mwh"].max() * 1.2])
l, r = st.columns(2, gap="large")
with l:
    theme.chart(theme.style(forest, f"Error difference · {FOLD_LABEL[fold]}", "", 330), key="forest")
with r:
    theme.chart(theme.style(adj, f"Grid-plan adjustment per hour · {FOLD_LABEL[fold]}", "MWh per hour", 330), key="adj")

# --- Training window --------------------------------------------------------------------------------
theme.section(
    "Does a shorter, more recent history help?",
    "Both 2026 runs predict the same January–June hours. One keeps 2020 in training, the other drops it.",
)
table = pd.DataFrame({
    "Site": [SITE_SHORT[s] for s in SITES],
    "Previous day": [overall.loc[("recent_2026", s, "previous_day")] for s in SITES],
    "Past average (2021–2025)": [overall.loc[("recent_2026", s, "training_climatology")] for s in SITES],
    "XGBoost 2020–2025": [overall.loc[("rolling_2026", s, "xgboost")] for s in SITES],
    "XGBoost 2021–2025": [overall.loc[("recent_2026", s, "xgboost")] for s in SITES],
})
table["Change"] = (table["XGBoost 2021–2025"] / table["XGBoost 2020–2025"] - 1).map("{:+.1%}".format)
st.dataframe(table, hide_index=True, width="stretch",
             column_config={k: st.column_config.NumberColumn(format="%.4f MW") for k in table.columns[1:5]})
theme.note(
    "Dropping 2020 helps Laoag and General Santos slightly and hurts Mactan. A shorter window is not reliably better, "
    "so the main results keep every available year. Reference output is modeled from NASA POWER weather, not metered; "
    "intervals are conditional on the fitted models and do not include physical-model uncertainty. "
    "July–September 2026 is not scored because NASA had not released the solar inputs when the test was run."
)
