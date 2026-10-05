"""SolWind: solar-wind forecasting and grid planning for three Philippine sites.

Run locally with:  streamlit run streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "solwind" / "assets"
PAGES = ROOT / "app_pages"

st.set_page_config(
    page_title="SolWind",
    page_icon=str(ASSETS / "icon.svg"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Streamlit Cloud pulls new commits into the running process. Page scripts rerun from the new files, but the
# solwind package stays imported, so a page could ask for a name the old module does not have (ImportError).
# Drop the package from sys.modules whenever one of its files changes, so it is imported fresh.
@st.cache_resource
def _package_mtimes() -> dict:
    return {}


_seen, _stale = _package_mtimes(), False
for _path in (ROOT / "solwind").glob("*.py"):
    _mtime = _path.stat().st_mtime
    if _seen.setdefault(_path.name, _mtime) != _mtime:
        _seen[_path.name], _stale = _mtime, True
if _stale:
    for _name in [n for n in sys.modules if n == "solwind" or n.startswith("solwind.")]:
        del sys.modules[_name]

from solwind import theme  # noqa: E402  (after set_page_config)
from solwind.data import DEFAULTS  # noqa: E402

# Keep the system design when moving between pages: Streamlit forgets widget
# state for widgets that are not on the current page unless it is re-assigned.
for key, value in DEFAULTS.items():
    st.session_state[key] = st.session_state.get(key, value)
for key in ["plant_date", "outage_day", "fc_date", "fc_source", "fc_model", "plan_date", "plan_model", "roll_fold", "roll_day", "audit_view"]:
    if key in st.session_state:
        st.session_state[key] = st.session_state[key]

theme.inject()
st.logo(str(ASSETS / "logo.svg"), icon_image=str(ASSETS / "icon.svg"), size="large")

navigation = st.navigation(
    {
        "": [
            st.Page(PAGES / "map.py", title="Map", icon=":material/map:", default=True),
            st.Page(PAGES / "plant.py", title="Live plant", icon=":material/bolt:", url_path="plant"),
            st.Page(PAGES / "designer.py", title="System designer", icon=":material/tune:", url_path="designer"),
            st.Page(PAGES / "sites.py", title="Compare sites", icon=":material/compare_arrows:", url_path="sites"),
        ],
        "Forecasting": [
            st.Page(PAGES / "forecast.py", title="Forecast accuracy", icon=":material/query_stats:", url_path="forecast"),
            st.Page(PAGES / "planning.py", title="Grid planning", icon=":material/event_repeat:", url_path="planning"),
            st.Page(PAGES / "rolling.py", title="Rolling test", icon=":material/date_range:", url_path="rolling"),
            st.Page(PAGES / "audit.py", title="2026 audit", icon=":material/fact_check:", url_path="audit"),
        ],
        "Reference": [
            st.Page(PAGES / "methods.py", title="Methodology", icon=":material/menu_book:", url_path="methods"),
        ],
    },
    position="top",
)

navigation.run()
