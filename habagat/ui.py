"""Shared controls."""

from __future__ import annotations

import streamlit as st

from habagat.data import DEFAULTS, MODEL_LABEL, MODELS, SITE_SHORT, SITES


def _keep_site() -> None:
    # Segmented controls can be clicked off; never leave the app without a site.
    if st.session_state.get("site") is None:
        st.session_state.site = st.session_state.get("_last_site", DEFAULTS["site"])
    st.session_state._last_site = st.session_state.site


def site_picker(label: str = "Site") -> str:
    st.segmented_control(
        label, SITES, key="site", format_func=SITE_SHORT.get, on_change=_keep_site, width="stretch"
    )
    return st.session_state.site or DEFAULTS["site"]


def model_picker(key: str, label: str = "Forecast method") -> str:
    st.session_state.setdefault(key, "xgboost")
    st.segmented_control(label, MODELS, key=key, format_func=MODEL_LABEL.get, width="stretch")
    return st.session_state[key] or "xgboost"
