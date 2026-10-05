"""Visual identity: tokens, a little CSS, and the Plotly template.

A field datasheet: white paper, graphite ink, hairline rules, no cards or shadows.
Colour is reserved for data: amber = solar, blue = wind, green = demand met by renewables,
red = grid import, violet = battery. Forecasts: XGBoost in blue, the two baselines in grey,
what actually happened in ink.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

PAPER = "#FFFFFF"      # background
SURFACE = "#F4F5F3"
RULE = "#E1E4E0"
INK = "#15191C"        # foreground
INK_SOFT = "#60686E"
HI = "#15191C"         # selection / XGBoost forecast
SUN = "#E8A317"        # solar
SUN_DEEP = "#B57A00"
SEA = "#2F6FDE"        # wind
LEAF = "#3BA272"       # renewables served
EMBER = "#D64545"      # grid
VIOLET = "#7C5CDB"     # battery
STONE = "#A3AAAE"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SOURCE_COLOR = {"solar": SUN, "wind": SEA, "combined": INK}
SITE_COLOR = {"Laoag, Ilocos Norte": SEA, "Mactan, Cebu": SUN, "General Santos City": LEAF}
MODEL_COLOR = {"xgboost": SEA, "previous_day": "#8A9297", "training_climatology": "#C4C9CC"}
DIVERGING = [[0, EMBER], [0.5, "#F4F5F3"], [1, LEAF]]

FONT_BODY = "Archivo, Helvetica, Arial, sans-serif"
FONT_MONO = "JetBrains Mono, ui-monospace, monospace"
FONT_HEAD = FONT_BODY

CSS = """
<style>
[data-testid="stMainBlockContainer"] { max-width:1320px; padding-top:4rem; padding-bottom:3rem; }
[data-testid="stHeader"] { background:#FFFFFF; border-bottom:1px solid #E1E4E0; }
[data-testid="stDecoration"] { display:none; }
h2 { letter-spacing:-.02em; }
h4 { font-size:1rem !important; letter-spacing:-.005em; border-top:1px solid #15191C; padding-top:.7rem !important; margin-top:1.6rem; }
[data-testid="stMetric"] { border-top:1px solid #E1E4E0; padding:.5rem 0 .2rem; }
[data-testid="stMetricLabel"] p { color:#60686E; font-size:.82rem !important; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * { font-family:'JetBrains Mono', monospace !important;
  font-size:1.7rem !important; font-weight:500; letter-spacing:-.03em; }
[data-testid="stPlotlyChart"] { border-top:1px solid #E1E4E0; }
[data-testid="stCaptionContainer"] { color:#60686E; }
.hb-desc { color:#60686E; margin:-.6rem 0 1.1rem; max-width:680px; line-height:1.45; font-size:.95rem; }
.hb-note { color:#60686E; font-size:.86rem; line-height:1.45; max-width:760px; margin:.2rem 0 .6rem; }
.hb-note b { color:#15191C; font-weight:600; }
</style>
"""


def html(markup: str) -> None:
    """Render trusted inline HTML. Whitespace is collapsed so markdown leaves it alone."""
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def inject() -> None:
    html(CSS)


def _template() -> go.layout.Template:
    axis = dict(
        gridcolor="#ECEEEB",
        linecolor="#C9CEC9",
        zeroline=False,
        automargin=True,
        title=dict(font=dict(size=12, color=INK_SOFT)),
        tickfont=dict(family=FONT_MONO, size=11, color=INK_SOFT),
    )
    return go.layout.Template(
        layout=dict(
            font=dict(family=FONT_BODY, color=INK, size=13),
            title=dict(font=dict(family=FONT_HEAD, size=15, color=INK, weight=600), x=0.01, xanchor="left", y=.96),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            colorway=[SUN, SEA, LEAF, EMBER, VIOLET, STONE],
            xaxis=axis,
            yaxis=axis,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                        font=dict(size=12, color=INK_SOFT), bgcolor="rgba(0,0,0,0)"),
            hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=RULE, font=dict(family=FONT_BODY, color=INK, size=12)),
            margin=dict(l=16, r=16, t=56, b=16),
            hovermode="x unified",
        )
    )


pio.templates["solwind"] = _template()
pio.templates.default = "solwind"


def style(fig: go.Figure, title: str = "", y: str = "", height: int = 380) -> go.Figure:
    fig.update_layout(title=title, height=height, plot_bgcolor=PAPER, paper_bgcolor=PAPER)
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
