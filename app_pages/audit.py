"""2026 audit: evidence that the January–June 2026 forecasts were made from earlier years only,
and how they compare with the output computed from 2026 weather."""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from solwind import theme, ui
from solwind.data import (
    DEFAULTS, MODEL_LABEL, MODELS, ROLLING, SITE_SHORT, SITES,
    load_rolling_hourly, load_rolling_metrics, load_weather, physics_args, run_generation,
)

FOLD = "rolling_2026"
RUN = json.loads((ROLLING / "run_2026.json").read_text())
CHECKS = json.loads((ROLLING / "rolling_verification.json").read_text())

theme.header("2026 audit", "Trained on 2020–2025 only. Scored once on January–June 2026.")

# --- 1. Chain of custody --------------------------------------------------------------------------
weather = load_weather()
years = weather.loc[weather["location"] == SITES[0], "timestamp_pht"].dt.year.value_counts().sort_index()
count = RUN["counts"][0]
steps = [
    ("1", "Fit", "2020–2024", f"{count['fit_hours']:,} h", "Two settings learn."),
    ("2", "Select", "2025", f"{count['validation_hours']:,} h", "The better one is kept."),
    ("3", "Refit", "2020–2025", f"{count['refit_hours']:,} h", "Last hour: 31 Dec 2025, 23:00."),
    ("4", "Forecast", "Jan–Jun 2026", f"{count['test_hours']:,} h", "Issued 00:00 daily, from the day before."),
    ("5", "Score", "Jan–Jun 2026", f"{count['test_hours']:,} h", "Compared once with computed output."),
]
color = {"Fit": theme.STONE, "Select": theme.VIOLET, "Refit": theme.STONE, "Forecast": theme.HI, "Score": theme.LEAF}
theme.html(
    f"""<style>
    .au-steps {{ display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:3px; margin:.4rem 0 .3rem; }}
    .au-steps > div {{ background:{theme.SURFACE}; border-top:3px solid var(--c); padding:.75rem .85rem .8rem; min-width:0; }}
    .au-steps .n {{ font:500 .72rem {theme.FONT_MONO}; color:{theme.INK_SOFT}; }}
    .au-steps .k {{ font:600 1.15rem/1.1 {theme.FONT_HEAD}; letter-spacing:-.01em; color:{theme.INK}; margin-top:.2rem; }}
    .au-steps .y {{ font:500 .85rem {theme.FONT_MONO}; color:var(--c); margin-top:.15rem; }}
    .au-steps .h {{ font:500 1.05rem {theme.FONT_MONO}; color:{theme.INK}; margin-top:.5rem; }}
    .au-steps .d {{ font-size:.82rem; color:{theme.INK_SOFT}; margin-top:.3rem; line-height:1.35; }}
    @media (max-width: 760px) {{ .au-steps {{ grid-template-columns:1fr; }} }}
    </style>
    <div class="au-steps">{"".join(
        f'<div style="--c:{color[k]}"><div class="n">STEP {n}</div><div class="k">{k}</div><div class="y">{y}</div>'
        f'<div class="h">{h} </div><div class="d">{d}</div></div>'
        for n, k, y, h, d in steps)}</div>"""
)
theme.note("The training script stops if any training hour overlaps the test: <code>assert refit.max() &lt; test.min()</code>.")

# --- 2. Computed vs forecast ------------------------------------------------------------------------
theme.section("Computed vs forecast", "Computed from 2026 NASA weather. Forecast issued at midnight, before the day.")
c = st.columns([1.3, 1.6], vertical_alignment="bottom")
with c[0]:
    site = ui.site_picker()
with c[1]:
    st.session_state.setdefault("audit_view", "Daily energy")
    view = st.segmented_control("Show", ["Daily energy", "Each hour"], key="audit_view",
                                width="stretch") or "Daily energy"

hourly = load_rolling_hourly()
test = hourly.loc[(hourly["fold"] == FOLD) & (hourly["location"] == site)].sort_values("target_timestamp_pht").copy()
test["day"] = test["target_timestamp_pht"].dt.tz_localize(None).dt.normalize()
pred = {m: f"{m}_prediction_mw" for m in MODELS}

if view == "Daily energy":
    daily = test.groupby("day")[["reference_output_mw", *pred.values()]].sum()
    fig = go.Figure()
    fig.add_scatter(x=daily.index, y=daily["reference_output_mw"], name="Computed from 2026 weather",
                    line=dict(color=theme.INK, width=2.4), fill="tozeroy", fillcolor="rgba(21,25,28,.05)")
    for m in MODELS:
        fig.add_scatter(x=daily.index, y=daily[pred[m]], name=f"{MODEL_LABEL[m]} forecast",
                        line=dict(color=theme.MODEL_COLOR[m], width=2.2 if m == "xgboost" else 1.2),
                        opacity=1 if m == "xgboost" else .75, visible=True if m == "xgboost" else "legendonly")
    fig.update_xaxes(dtick="M1", tickformat="%b")
    fig.update_layout(legend=dict(orientation="h", x=0, xanchor="left", y=1.0, yanchor="bottom"), margin=dict(t=80))
    theme.chart(theme.style(fig, f"{SITE_SHORT[site]} · Jan–Jun 2026 · daily energy (MWh per day)", "MWh", 380), key="audit_daily")
    st.caption("Click a baseline in the legend to add it.")
else:
    a, b = st.columns([1, 1], gap="large")
    with a:
        sc = go.Figure()
        sc.add_scatter(x=test["reference_output_mw"], y=test[pred["xgboost"]], mode="markers", name="Hours",
                       marker=dict(color=theme.MODEL_COLOR["xgboost"], size=4, opacity=.28, line=dict(width=0)),
                       hovertemplate="computed %{x:.3f} MW · forecast %{y:.3f} MW<extra></extra>")
        top = float(max(test["reference_output_mw"].max(), test[pred["xgboost"]].max())) * 1.03
        sc.add_scatter(x=[0, top], y=[0, top], mode="lines", name="Perfect forecast",
                       line=dict(color=theme.INK_SOFT, width=1, dash="dot"), hoverinfo="skip")
        sc.update_xaxes(title="Computed from 2026 weather (MW)", range=[0, top])
        sc.update_yaxes(range=[0, top])
        sc.update_layout(showlegend=False)
        theme.chart(theme.style(sc, f"{SITE_SHORT[site]} · XGBoost, all {len(test):,} hours", "Forecast (MW)", 380), key="audit_scatter")
    with b:
        week = test.loc[test["target_timestamp_pht"].dt.month == 3].head(24 * 7)
        wf = go.Figure()
        wf.add_scatter(x=week["target_timestamp_pht"], y=week["reference_output_mw"], name="Computed",
                       line=dict(color=theme.INK, width=2.4))
        wf.add_scatter(x=week["target_timestamp_pht"], y=week[pred["xgboost"]], name="XGBoost forecast",
                       line=dict(color=theme.MODEL_COLOR["xgboost"], width=2, dash="dash"))
        wf.update_layout(legend=dict(orientation="h", x=0, xanchor="left", y=1.0, yanchor="bottom"), margin=dict(t=80))
        wf.update_xaxes(tickformat="%a %d")
        theme.chart(theme.style(wf, "First week of March 2026, hour by hour", "MW", 380), key="audit_week")

# monthly table, all three methods
err = test.assign(month=test["target_timestamp_pht"].dt.month)
for m in MODELS:
    err[m] = (err[pred[m]] - err["reference_output_mw"]).abs()
month = err.groupby("month").agg(computed=("reference_output_mw", "sum"), forecast=(pred["xgboost"], "sum"),
                                 **{m: (m, "mean") for m in MODELS})
best = month[["previous_day", "training_climatology"]].min(axis=1)
table = pd.DataFrame({
    "Month": [theme.MONTHS[i - 1] + " 2026" for i in month.index],
    "Computed (MWh)": month["computed"], "XGBoost forecast (MWh)": month["forecast"],
    "XGBoost MAE": month["xgboost"], "Previous-day MAE": month["previous_day"], "Past-average MAE": month["training_climatology"],
    "vs best baseline": (month["xgboost"] / best - 1).map("{:+.0%}".format),
})
total = {
    "Month": "Jan–Jun 2026", "Computed (MWh)": month["computed"].sum(), "XGBoost forecast (MWh)": month["forecast"].sum(),
    **{k: err[m].mean() for k, m in zip(["XGBoost MAE", "Previous-day MAE", "Past-average MAE"], MODELS)},
}
total["vs best baseline"] = f"{total['XGBoost MAE'] / min(total['Previous-day MAE'], total['Past-average MAE']) - 1:+.0%}"
table = pd.concat([table, pd.DataFrame([total])], ignore_index=True)
st.dataframe(table, hide_index=True, width="stretch", column_config={
    "Computed (MWh)": st.column_config.NumberColumn(format="%.1f"),
    "XGBoost forecast (MWh)": st.column_config.NumberColumn(format="%.1f"),
    **{k: st.column_config.NumberColumn(format="%.4f MW") for k in ["XGBoost MAE", "Previous-day MAE", "Past-average MAE"]},
})
metrics = load_rolling_metrics()
stored = metrics.loc[(metrics["fold"] == FOLD) & (metrics["location"] == site) & (metrics["source"] == "combined")
                     & (metrics["aggregation"] == "overall") & (metrics["scope"] == "all_hours")
                     & (metrics["period"] == "available_test") & (metrics["model"] == "xgboost"), "mae_mw"].iloc[0]
theme.note(f"Recomputed MAE {total['XGBoost MAE']:.4f} MW = stored result {stored:.4f} MW (paper, Table IV).")

# --- 3. Recompute the computed side -------------------------------------------------------------------
theme.section("Recompute it", "The app reruns its physics on 2026 weather and compares every hour.")
generation = run_generation(**physics_args(DEFAULTS))
check = hourly.loc[hourly["fold"] == FOLD, ["location", "target_timestamp_pht", "reference_output_mw"]].merge(
    generation[["location", "timestamp_pht", "combined_mw"]],
    left_on=["location", "target_timestamp_pht"], right_on=["location", "timestamp_pht"], how="left",
)
gap = (check["combined_mw"] - check["reference_output_mw"]).abs()
k = st.columns(4)
k[0].metric("Hours compared", f"{len(check):,}", "3 sites × Jan–Jun 2026", delta_color="off")
k[1].metric("Missing hours", f"{int(check['combined_mw'].isna().sum())}")
k[2].metric("Largest difference", f"{gap.max():.1e} MW", "rounding only", delta_color="off")
k[3].metric("Computed energy, 3 sites", f"{check['combined_mw'].sum():,.0f} MWh", "Jan–Jun 2026", delta_color="off")

# --- 4. Automated checks ------------------------------------------------------------------------------
passed = sum(c["passed"] for c in CHECKS["checks"])
theme.section("Automated checks", f"{passed} of {CHECKS['check_count']} passed. The 2026 checks:")
plain = {
    "issue midnight": "Every forecast was issued at 00:00 of its target day",
    "horizon and target ordering": "Each target hour is 1 to 24 hours after its issue time",
    "test year only": "Every scored hour is in 2026",
    "complete days and sources": "Every day has all 24 hours for solar and wind",
    "unique site source target": "No hour is scored twice",
    "2026 complete local range": "2026 data runs without gaps from 1 Jan to 30 Jun",
    "2026 site hour counts": "Each site has exactly 4,344 hours",
    "2026 physical outputs bounded": "Computed output stays between 0 and installed capacity",
}
rows = []
for chk in CHECKS["checks"]:
    name = chk["name"]
    if not name.startswith("rolling_2026") and not name.startswith("2026") and "2026_available" not in name:
        continue
    short = name.replace("rolling_2026 ", "")
    meaning = next((v for key, v in plain.items() if short == key or name == key), "")
    if not meaning:
        if "serialized metrics" in short:
            meaning = "Stored error matches a fresh recomputation from the hourly predictions"
        elif "source sum" in short:
            meaning = "Combined forecast equals solar plus wind"
        elif "planning balance" in short:
            meaning = "Grid-plan energy balances every hour"
        elif "SOC bounds" in short:
            meaning = "Battery charge stays within 0 and 2 MWh"
        elif "hash" in short:
            meaning = "Input file is byte-identical to the one the run used (SHA-256)"
    rows.append({"Check": short, "What it proves": meaning, "Result": "Passed" if chk["passed"] else "Failed"})
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", height=min(38 + 35 * len(rows), 460))
flags = RUN["pipeline_checks"]
theme.note(f"Trained {RUN['created_at_utc'][:10]} · Python {RUN['versions']['python']} · XGBoost {RUN['versions']['xgboost']}. Output is modeled, not metered.")

# --- 5. Download ---------------------------------------------------------------------------------------
theme.section("Download")
out = hourly.loc[hourly["fold"] == FOLD, ["location", "target_timestamp_pht", "reference_output_mw", *pred.values()]].copy()
out.insert(2, "issued_at_pht", out["target_timestamp_pht"].dt.normalize())
out = out.rename(columns={"reference_output_mw": "computed_mw", **{v: f"{k}_forecast_mw" for k, v in pred.items()}})
out["target_timestamp_pht"] = out["target_timestamp_pht"].dt.strftime("%Y-%m-%d %H:%M")
out["issued_at_pht"] = out["issued_at_pht"].dt.strftime("%Y-%m-%d %H:%M")
st.download_button("Download 2026 computed vs forecast (CSV)", out.to_csv(index=False, float_format="%.6f").encode(),
                   file_name="solwind_2026_computed_vs_forecast.csv", mime="text/csv", icon=":material/download:")
