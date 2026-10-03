"""Every page renders without exceptions (Streamlit AppTest, headless)."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
PAGES = ["overview", "plant", "designer", "sites", "forecast", "planning", "methods"]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page: str) -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=120)
    app.run()
    if page != "overview":
        app.switch_page(f"app_pages/{page}.py")
        app.run()
    assert not app.exception, [e.message for e in app.exception]


@pytest.mark.parametrize("page", ["plant", "designer", "sites", "planning"])
def test_custom_design_renders_everywhere(page: str) -> None:
    # A non-default design (no wind, big battery, another site) must work on every page that uses it.
    # AppTest cannot round-trip segmented controls, so the design is set directly in session state.
    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=120)
    app.session_state["battery_capacity"] = 6.0
    app.session_state["wind_capacity"] = 0.0
    app.session_state["site"] = "General Santos City"
    app.run()
    app.switch_page(f"app_pages/{page}.py").run()
    assert not app.exception, [e.message for e in app.exception]
    assert app.session_state["battery_capacity"] == 6.0
