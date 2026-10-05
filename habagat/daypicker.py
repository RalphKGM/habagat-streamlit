"""Day picker component: energy-coloured calendar, full-range ribbon, presets and typed dates.

Front end: assets/daypicker (plain HTML/JS, no build step). The same daypicker.js also powers
the calendar that opens from the Map's timeline.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from habagat.data import SITE_SHORT, current_dispatch, settings

_picker = components.declare_component("habagat_daypicker", path=str(Path(__file__).resolve().parent / "assets" / "daypicker"))


@st.cache_data(show_spinner=False, max_entries=16)
def _daily(frame_key: tuple, _frame: pd.DataFrame) -> dict:
    daily = (
        _frame.assign(day=_frame["timestamp_pht"].dt.date)
        .groupby("day")
        .agg(gen=("combined_mw", "sum"), wind=("wind_mw", "sum"), grid=("grid_import_mwh", "sum"))
    )
    return {
        "start": daily.index.min().isoformat(),
        "gen": daily["gen"].round(2).tolist(),
        "wind": daily["wind"].round(2).tolist(),
        "grid": daily["grid"].round(2).tolist(),
    }


def daily_series(site: str) -> dict:
    """Daily energy, wind and grid totals for every day on record, for the current design."""
    cfg = settings()
    frame = current_dispatch(site)
    return _daily((site, tuple(sorted(cfg.items()))), frame)


def day_picker(
    state_key: str, site: str, default: dt.date, key: str,
    first: dt.date | None = None, last: dt.date | None = None,
) -> dt.date:
    """Render the picker and keep ``st.session_state[state_key]`` (a date) in sync with it.

    ``first``/``last`` narrow the range to, for example, the 2025 forecast test.
    """
    series = daily_series(site)
    start = dt.date.fromisoformat(series["start"])
    end = start + dt.timedelta(days=len(series["gen"]) - 1)
    first, last = max(first or start, start), min(last or end, end)
    if (first, last) != (start, end):  # show only the selectable days in the ribbon, calendar and presets
        lo, hi = (first - start).days, (last - start).days + 1
        series = {"start": first.isoformat(), **{k: series[k][lo:hi] for k in ["gen", "wind", "grid"]}}
    value = st.session_state.get(state_key, default)
    value = min(max(value, first), last)
    st.session_state[state_key] = value
    event = _picker(daily=series, value=value.isoformat(), min=first.isoformat(), max=last.isoformat(),
                    site=SITE_SHORT[site], key=key, default=None)
    if event and event.get("nonce") != st.session_state.get(f"_{key}_nonce"):
        st.session_state[f"_{key}_nonce"] = event["nonce"]
        picked = dt.date.fromisoformat(event["date"])
        if picked != value:
            st.session_state[state_key] = picked
            st.rerun()
    return value
