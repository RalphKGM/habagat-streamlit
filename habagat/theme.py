"""Visual identity: tokens, a little CSS, and the Plotly template.

A night nautical chart: monsoon-blue surfaces, hairline rules, condensed instrument numerals.
Colour is reserved for data: coral = solar, cyan = wind, lilac = battery, rose = grid,
mint = renewables served, yellow = selection and the XGBoost forecast.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

PAPER = "#0C1E2B"      # background
SURFACE = "#0F2433"
RULE = "#1F3A4D"
INK = "#EAF2F6"        # foreground
INK_SOFT = "#8BA6B5"
HI = "#FFD166"         # selection / highlight
SUN = "#FF8A5B"        # solar
SUN_DEEP = "#E06A3F"
SEA = "#3FD0F0"        # wind
LEAF = "#6EE7B7"       # renewables served
EMBER = "#FF5C7A"      # grid
VIOLET = "#C3A6FF"     # battery
STONE = "#6F8796"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SOURCE_COLOR = {"solar": SUN, "wind": SEA, "combined": LEAF}
SITE_COLOR = {"Laoag, Ilocos Norte": SEA, "Mactan, Cebu": HI, "General Santos City": SUN}
MODEL_COLOR = {"xgboost": HI, "previous_day": VIOLET, "training_climatology": STONE}
DIVERGING = [[0, EMBER], [0.5, SURFACE], [1, LEAF]]

FONT_BODY = "Barlow, sans-serif"
FONT_MONO = "IBM Plex Mono, monospace"
FONT_HEAD = "Barlow Condensed, Barlow, sans-serif"

CSS = """
<style>
[data-testid="stMainBlockContainer"] { max-width:1360px; padding-top:4.2rem; padding-bottom:3rem; }
[data-testid="stHeader"] { background:#0A1925; border-bottom:1px solid #1F3A4D; }
[data-testid="stDecoration"] { display:none; }
h2 { text-transform:uppercase; letter-spacing:.03em; }
h4 { text-transform:uppercase; letter-spacing:.05em; font-size:1rem !important; color:#8BA6B5 !important; }
[data-testid="stMetric"] { border-top:2px solid #1F3A4D; padding:.55rem 0 .3rem; }
[data-testid="stMetricLabel"] p { color:#8BA6B5; font-size:.85rem !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { font-family:'Barlow Condensed', sans-serif !important;
  font-size:2.1rem !important; font-weight:600; }
[data-testid="stPlotlyChart"] { background:#0F2433; border:1px solid #1F3A4D; overflow:hidden; }
[data-testid="stCaptionContainer"] { color:#8BA6B5; }
.hb-desc { color:#8BA6B5; margin:-.5rem 0 1.2rem; max-width:780px; line-height:1.5; font-size:1rem; }
.hb-note { border-left:2px solid #FFD166; padding:.35rem .9rem; color:#8BA6B5; font-size:.92rem; line-height:1.5; }
.hb-note b { color:#EAF2F6; font-weight:500; }
</style>
"""


def html(markup: str) -> None:
    """Render trusted inline HTML. Whitespace is collapsed so markdown leaves it alone."""
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def inject() -> None:
    html(CSS)


def _template() -> go.layout.Template:
    axis = dict(
        gridcolor="#17344A",
        linecolor="#2A4B60",
        zeroline=False,
        automargin=True,
        title=dict(font=dict(size=12, color=INK_SOFT)),
        tickfont=dict(family=FONT_MONO, size=11, color=INK_SOFT),
    )
    return go.layout.Template(
        layout=dict(
            font=dict(family=FONT_BODY, color=INK, size=13),
            title=dict(font=dict(family=FONT_HEAD, size=17, color=INK), x=0.01, xanchor="left", y=.96),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            colorway=[SUN, SEA, LEAF, EMBER, VIOLET, STONE],
            xaxis=axis,
            yaxis=axis,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=12, color=INK_SOFT), bgcolor="rgba(0,0,0,0)"),
            hoverlabel=dict(bgcolor="#06121B", bordercolor=RULE, font=dict(family=FONT_BODY, color=INK, size=12)),
            margin=dict(l=16, r=16, t=56, b=16),
            hovermode="x unified",
        )
    )


pio.templates["habagat"] = _template()
pio.templates.default = "habagat"


def style(fig: go.Figure, title: str = "", y: str = "", height: int = 380) -> go.Figure:
    fig.update_layout(title=title, height=height)
    if y:
        fig.update_layout(yaxis_title=y)
    return fig


def chart(fig: go.Figure, key: str | None = None) -> None:
    st.plotly_chart(fig, key=key, config={"displayModeBar": False}, theme=None)


def header(title: str, description: str = "") -> None:
    st.markdown(f"## {title}")
    if description:
        html(f'<p class="hb-desc">{description}</p>')


def note(text: str) -> None:
    html(f'<div class="hb-note">{text}</div>')


def section(title: str, description: str = "") -> None:
    st.markdown(f"#### {title}")
    if description:
        html(f'<p class="hb-desc" style="margin-top:-.6rem">{description}</p>')
