"""Habagat: solar-wind forecasting and grid planning for three Philippine sites.

Run locally with:  streamlit run streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent / "habagat" / "assets"

st.set_page_config(
    page_title="Habagat · Solar-wind forecasting",
    page_icon=str(ASSETS / "icon.svg"),
    layout="wide",
    initial_sidebar_state="collapsed",
)

from habagat import theme  # noqa: E402  (after set_page_config)
from habagat.data import DEFAULTS  # noqa: E402

# Keep the system design when moving between pages: Streamlit forgets widget
# state for widgets that are not on the current page unless it is re-assigned.
for key, value in DEFAULTS.items():
    st.session_state[key] = st.session_state.get(key, value)
for key in ["plant_date", "fc_date", "fc_source", "fc_model", "plan_date", "plan_model"]:
    if key in st.session_state:
        st.session_state[key] = st.session_state[key]

theme.inject()
st.logo(str(ASSETS / "logo.svg"), icon_image=str(ASSETS / "icon.svg"), size="large")

PAGES = Path(__file__).resolve().parent / "app_pages"
navigation = st.navigation(
    [
        st.Page(PAGES / "overview.py", title="Overview", icon=":material/wb_sunny:", default=True),
        st.Page(PAGES / "plant.py", title="Live plant", icon=":material/electric_bolt:", url_path="plant"),
        st.Page(PAGES / "designer.py", title="System designer", icon=":material/tune:", url_path="designer"),
        st.Page(PAGES / "sites.py", title="Sites", icon=":material/map:", url_path="sites"),
        st.Page(PAGES / "forecast.py", title="Forecast lab", icon=":material/insights:", url_path="forecast"),
        st.Page(PAGES / "planning.py", title="Grid planning", icon=":material/event_repeat:", url_path="planning"),
        st.Page(PAGES / "methods.py", title="Methods", icon=":material/menu_book:", url_path="methods"),
    ],
    position="top",
)
navigation.run()
theme.footer()
