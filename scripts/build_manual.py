"""Build docs/SolWind_System_Users_Manual.pdf.

Layout follows the System User's Manual outline (General Information, System Summary, Getting Started,
Using the System, Querying, Reporting) with the content requirements of ISO/IEC/IEEE 26514:2022:
front matter, numbered task procedures, messages and troubleshooting, glossary and index. Text only.
Run: python scripts/build_manual.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Frame, KeepTogether, NextPageTemplate, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import SimpleIndex, TableOfContents

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "SolWind_System_Users_Manual.pdf"
VERSION = "1.0"
ISSUED = "October 2026"
URL = "https://habagat.streamlit.app"
REPO = "https://github.com/RalphKGM/habagat-streamlit"

FONTS = Path("/System/Library/Fonts/Supplemental")
for name, file in [("Serif", "Times New Roman.ttf"), ("Serif-Bold", "Times New Roman Bold.ttf"),
                   ("Serif-Italic", "Times New Roman Italic.ttf"), ("Serif-BoldItalic", "Times New Roman Bold Italic.ttf"),
                   ("Sans", "Arial.ttf"), ("Sans-Bold", "Arial Bold.ttf"), ("Mono", "Courier New.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-Bold", italic="Serif-Italic", boldItalic="Serif-BoldItalic")
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold")

BODY = ParagraphStyle("body", fontName="Serif", fontSize=11, leading=14.5, spaceAfter=7)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=9.5, leading=12, spaceAfter=0)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=10, leading=12.5, spaceAfter=0)
CELL_H = ParagraphStyle("cellh", parent=CELL, fontName="Sans-Bold", fontSize=9.5)
H1 = ParagraphStyle("h1", fontName="Sans-Bold", fontSize=16, leading=20, spaceBefore=0, spaceAfter=12)
FRONT = ParagraphStyle("front", parent=H1)  # front-matter headings stay out of the contents
H2 = ParagraphStyle("h2", fontName="Sans-Bold", fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=6)
H3 = ParagraphStyle("h3", fontName="Sans-Bold", fontSize=11, leading=14, spaceBefore=8, spaceAfter=4)
STEP = ParagraphStyle("step", parent=BODY, leftIndent=22, bulletIndent=4, spaceAfter=4)
BULLET = ParagraphStyle("bullet", parent=BODY, leftIndent=18, bulletIndent=6, spaceAfter=3)
NOTE = ParagraphStyle("note", parent=BODY, leftIndent=18, rightIndent=18)
CODE = ParagraphStyle("code", fontName="Mono", fontSize=9.5, leading=12.5, leftIndent=18, spaceAfter=8)
TITLE = ParagraphStyle("title", fontName="Sans-Bold", fontSize=28, leading=34, alignment=TA_CENTER)
SUBTITLE = ParagraphStyle("subtitle", fontName="Sans", fontSize=16, leading=22, alignment=TA_CENTER)
CENTER = ParagraphStyle("center", parent=BODY, alignment=TA_CENTER)

INDEX = SimpleIndex(dot=" . ", headers=True, style=[
    ParagraphStyle("ix0", fontName="Serif", fontSize=10.5, leading=13.5),
    ParagraphStyle("ix1", fontName="Serif", fontSize=10.5, leading=13.5, leftIndent=18),
])


class Manual(BaseDocTemplate):
    """Numbered headings feed the table of contents and the PDF outline."""

    def __init__(self, path: str):
        super().__init__(path, pagesize=letter, leftMargin=inch, rightMargin=inch, topMargin=inch,
                         bottomMargin=inch, title="SolWind System User's Manual", author="SolWind",
                         subject=f"Version {VERSION}, {ISSUED}", creator="SolWind")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate("cover", [frame], onPage=lambda c, d: None),
                               PageTemplate("body", [frame], onPage=self._furniture)])
        self._n = 0

    def beforeDocument(self):
        self._n = 0

    def _furniture(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Sans", 8.5)
        top = letter[1] - 0.6 * inch
        canvas.drawString(inch, top, "SolWind System User's Manual")
        canvas.drawRightString(letter[0] - inch, top, f"Version {VERSION}")
        canvas.setLineWidth(0.5)
        canvas.line(inch, top - 5, letter[0] - inch, top - 5)
        canvas.line(inch, 0.75 * inch, letter[0] - inch, 0.75 * inch)
        canvas.drawString(inch, 0.58 * inch, ISSUED)
        canvas.drawRightString(letter[0] - inch, 0.58 * inch, f"Page {doc.page}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph) or flowable.style.name not in ("h1", "h2"):
            return
        text = flowable.getPlainText()
        level = 0 if flowable.style.name == "h1" else 1
        key = f"h{self._n}"
        self._n += 1
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=level > 0)
        self.notify("TOCEntry", (level, text, self.page, key))


story: list = []


def h1(text: str):
    story.append(PageBreak())
    story.append(Paragraph(text, H1))


def h2(text: str):
    story.append(CondPageBreak(1.3 * inch))
    story.append(Paragraph(text, H2))


def h3(text: str):
    story.append(CondPageBreak(1.0 * inch))
    story.append(Paragraph(text, H3))


def p(text: str, style=BODY):
    story.append(Paragraph(text, style))


def ix(*terms: str) -> str:
    """Invisible index markers, placed at the start of a paragraph."""
    return "".join(f'<index item="{t}"/>' for t in terms)


def bullets(*items: str):
    for it in items:
        story.append(Paragraph(it, BULLET, bulletText="•"))


def steps(*items: str):
    for i, it in enumerate(items, 1):
        story.append(Paragraph(it, STEP, bulletText=f"{i}."))
    story.append(Spacer(1, 4))


def note(label: str, text: str):
    p(f"<b>{label}:</b> {text}", NOTE)


def table(rows: list[list[str]], widths: list[float], keep: bool = False):
    data = [[Paragraph(c, CELL_H if r == 0 else CELL) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=[w * inch for w in widths], repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E6E6E6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(KeepTogether(t) if keep else t)
    story.append(Spacer(1, 10))


def code(*lines: str):
    p("<br/>".join(lines), CODE)


# --- Cover -------------------------------------------------------------------------------------------
story += [Spacer(1, 2.2 * inch), Paragraph("SolWind", TITLE), Spacer(1, 14),
          Paragraph("System User's Manual", SUBTITLE), Spacer(1, 10),
          Paragraph("Hourly solar, wind and battery simulation with day-ahead forecasting<br/>"
                    "for three Philippine sites", CENTER),
          Spacer(1, 2.4 * inch),
          Paragraph(f"Version {VERSION}<br/>{ISSUED}", CENTER), Spacer(1, 10),
          Paragraph(URL, CENTER),
          NextPageTemplate("body")]

# --- Document control --------------------------------------------------------------------------------
story.append(PageBreak())
p("Document Control", FRONT)
table([
    ["Item", "Detail"],
    ["Document", "SolWind System User's Manual"],
    ["Version", VERSION],
    ["Date of issue", ISSUED],
    ["Applies to", "SolWind web application, release of October 2026 (data from 1 January 2020 to 30 June 2026)"],
    ["Hosted address", URL],
    ["Source code", REPO],
], [1.6, 4.9])
p("Revision History", ParagraphStyle("fronth2", parent=H2))
table([
    ["Version", "Date", "Description"],
    ["1.0", ISSUED, "First issue. Covers all nine pages of the application, local installation, downloads, "
                    "messages and troubleshooting."],
], [0.9, 1.3, 4.3])
p("Notice", ParagraphStyle("fronth2b", parent=H2))
p("All energy figures in SolWind are modeled from NASA POWER weather data using fixed engineering equations. "
  "They are not metered plant output. SolWind is intended for study, comparison and planning exercises. It must "
  "not be used as the sole basis for operating a power plant or dispatching a grid.")

# --- Contents ----------------------------------------------------------------------------------------
story.append(PageBreak())
p("Table of Contents", FRONT)
toc = TableOfContents(dotsMinLevel=0)
toc.levelStyles = [
    ParagraphStyle("toc0", fontName="Sans-Bold", fontSize=10.5, leading=15, spaceBefore=5),
    ParagraphStyle("toc1", fontName="Serif", fontSize=10.5, leading=13.5, leftIndent=20),
]
story.append(toc)

# === 1 General Information =============================================================================
h1("1  General Information")
h2("1.1  System Overview")
p(ix("overview") + "SolWind is a web application that simulates a 1 MW solar photovoltaic (PV) plant, a 1 MW "
  "wind turbine and a 2 MWh battery, hour by hour, at three Philippine sites from 1 January 2020 to "
  "30 June 2026. It also scores day-ahead forecasts of that output and shows how forecast error changes "
  "an hourly grid-purchase plan.")
p("With SolWind you can:")
bullets("replay any day at any site and watch output, demand and battery charge change hour by hour;",
        "resize the plant and battery and rerun every hour of the record;",
        "compare the three sites on energy, seasonality and wind;",
        "inspect day-ahead forecast accuracy for 2025 and January to June 2026;",
        "download hourly results as CSV files.")
table([
    ["Site", "Island group", "Coordinates"],
    ["Laoag, Ilocos Norte", "Luzon", "18.18° N, 120.53° E"],
    ["Mactan, Cebu", "Visayas", "10.32° N, 123.98° E"],
    ["General Santos City", "Mindanao", "6.06° N, 125.10° E"],
], [2.4, 1.6, 2.5], keep=True)

h2("1.2  Intended Audience")
p("This manual is for energy planners, engineers, analysts, instructors and students who use SolWind to study "
  "hybrid solar and wind generation. It assumes you can use a web browser. Section 3.2 assumes basic familiarity "
  "with installing software. No programming is needed to use the application.")

h2("1.3  Project References")
table([
    ["Reference", "Description"],
    ["SolWind technical paper", "“Day Ahead Forecasting of Modeled Solar and Wind Generation and Battery Planning in "
                                "Three Philippine Locations” (IEEE conference format). Describes the equations, "
                                "forecasting method and results in full."],
    ["Methodology page", "The Methodology page inside SolWind (Section 4.9) lists the equations, fixed parameters, "
                         "sources and limitations."],
    ["Source repository", REPO],
    ["NASA POWER", "NASA Prediction Of Worldwide Energy Resources, hourly data. https://power.larc.nasa.gov"],
], [1.8, 4.7])

h2("1.4  Authorized Use")
p(ix("authorized use") + "SolWind is open to anyone with the address. No account is needed. The weather data comes from "
  "NASA POWER, which is free to use with attribution. Results may be quoted or reproduced if SolWind and NASA "
  "POWER are credited and the results are described as modeled, not measured.")

h2("1.5  Points of Contact")
p(ix("support") + "Report problems, questions and suggestions by opening an issue in the source repository: "
  f"{REPO}/issues. Include the page name, the site and day selected, and what you expected to see.")

h2("1.6  Organization of the Manual")
table([
    ["Section", "Contents"],
    ["1  General Information", "Purpose, audience, references and conventions."],
    ["2  System Summary", "Configuration, data flow, access and alternate modes of operation."],
    ["3  Getting Started", "Opening the hosted system, installing it locally, the menu and shared controls."],
    ["4  Using the System", "Each page in turn: purpose, controls, results and procedures."],
    ["5  Querying", "Choosing a site, day, source and method to answer a specific question."],
    ["6  Reporting", "Downloading results and the contents of each file."],
    ["7  Messages and Troubleshooting", "On-screen messages, problems and fixes, frequent questions."],
    ["Appendices", "Glossary, standard design parameters and index."],
], [2.2, 4.3])

h2("1.7  Document Conventions")
table([
    ["Convention", "Meaning", "Example"],
    ["<b>Bold</b>", "A page, button, menu or control you click or set.", "Select <b>Reset to standard design</b>."],
    ["<i>Italic</i>", "An option within a control, or a term defined in the glossary.", "Set <b>Show</b> to <i>Each hour</i>."],
    ['<font name="Mono">Monospace</font>', "Text you type, a file name or a command.", '<font name="Mono">streamlit run streamlit_app.py</font>'],
    ["A > B", "Open menu A, then select item B.", "<b>Forecasting > Rolling test</b>"],
    ["Note", "Information that helps you avoid a mistake or misreading.", "—"],
], [1.3, 2.9, 2.3])
p("Times are Philippine Standard Time (PHT, UTC+8). Power is in megawatts (MW), energy in megawatt-hours (MWh).")

h2("1.8  Acronyms and Abbreviations")
table([
    ["Term", "Meaning"],
    ["CSV", "Comma-separated values (a spreadsheet-readable text file)"],
    ["MAE", "Mean absolute error"],
    ["MW / MWh", "Megawatt / megawatt-hour"],
    ["NASA POWER", "NASA Prediction Of Worldwide Energy Resources"],
    ["PHT", "Philippine Standard Time, UTC+8"],
    ["PV", "Photovoltaic (solar panel)"],
    ["SOC", "State of charge of the battery"],
    ["XGBoost", "Extreme Gradient Boosting, the machine-learning forecasting method"],
], [1.5, 5.0])

# === 2 System Summary ==================================================================================
h1("2  System Summary")
h2("2.1  System Configuration")
p(ix("system requirements") + "SolWind runs in a web browser. It can be used from the hosted address or run on your own computer.")
table([
    ["Component", "Requirement"],
    ["Browser", "A current version of Chrome, Edge, Firefox or Safari, with JavaScript enabled. A screen at least "
                "1280 pixels wide is recommended. Below 760 pixels the Map switches to a stacked phone layout."],
    ["Network", "An internet connection for the hosted address. A local copy needs a connection only for its first start."],
    ["Local computer (optional)", "macOS, Windows or Linux with Python 3.9 to 3.12 and about 500 MB of free disk space."],
    ["Python packages", "streamlit 1.50 or later, plotly, pandas, numpy and pyarrow, installed automatically from "
                        '<font name="Mono">requirements.txt</font>.'],
], [1.8, 4.7])

h2("2.2  Data Flows")
p(ix("data flow") + "Data moves through SolWind in five stages. All data ships with the application. Nothing is downloaded "
  "while you use it.")
steps("<b>Weather.</b> Hourly NASA POWER irradiance, temperature and wind for each site, 1 January 2020 to "
      "30 June 2026 (56,952 hours per site).",
      "<b>Generation.</b> Fixed equations turn weather into solar and wind output for the current design.",
      "<b>Dispatch.</b> Each hour, generation serves the standard demand profile first. Surplus charges the battery, "
      "a shortfall is met from the battery, then from the grid.",
      "<b>Forecasts.</b> Stored day-ahead forecasts from three methods, issued at 00:00 for each day, are compared "
      "with the generated output.",
      "<b>Pages and downloads.</b> Results are shown as charts, tables and figures, and can be downloaded as CSV files.")
note("Note", "Forecasts are scored against the standard 1 MW + 1 MW design. Changing the design in System designer does "
     "not change the stored forecast results.")

h2("2.3  User Access Levels")
p(ix("access levels") + "SolWind has one access level. Every visitor can view every page and download every file. There are no "
  "accounts or passwords. Settings you choose, such as site, design and day, last only for your browser "
  "session and are not seen by other users.")

h2("2.4  Contingencies and Alternate Modes of Operation")
table([
    ["Situation", "Alternate mode"],
    ["The hosted address is asleep", "Select the wake-up button and wait about 30 seconds (Section 7.2)."],
    ["The hosted address is unavailable", "Run SolWind locally (Section 3.2). The local copy contains all data and "
                                          "works offline after its first start."],
    ["A page shows an error", "Reload the page. If the error remains, restart the application or report it (Section 1.5)."],
], [2.3, 4.2])

# === 3 Getting Started =================================================================================
h1("3  Getting Started")
h2("3.1  Opening the Hosted System")
steps(f'Open a browser and go to <font name="Mono">{URL}</font>.',
      "If a wake-up screen appears, select the button and wait for the application to start.",
      "The <b>Map</b> page opens. The first page can take a few seconds while the hourly results are calculated. "
      "Later pages open at once.")

h2("3.2  Installing and Running Locally")
p(ix("installation") + "<b>Using the start file (macOS or Windows)</b>")
steps(f"Download the source code from {REPO} (<b>Code > Download ZIP</b>) and unzip it, or clone the repository.",
      'On macOS, double-click <font name="Mono">Run SolWind.command</font>. On Windows, double-click '
      '<font name="Mono">Run SolWind.bat</font>.',
      "Wait while the first start installs the required packages. This needs an internet connection and takes a "
      "few minutes.",
      'Your browser opens SolWind at <font name="Mono">http://localhost:8501</font>.')
note("Note", "If macOS says the file cannot be opened, right-click it, select <b>Open</b>, then confirm.")
p("<b>Using a terminal</b>")
code("python -m venv .venv",
     "source .venv/bin/activate          # Windows: .venv\\Scripts\\activate",
     "pip install -r requirements.txt",
     "streamlit run streamlit_app.py")

h2("3.3  System Menu")
p(ix("menu") + "The bar across the top of every page is the system menu. Select a page name to open it. Pages are grouped as follows.")
table([
    ["Menu group", "Page", "Purpose", "Section"],
    ["(main)", "Map", "All three sites on one day, hour by hour", "4.1"],
    ["(main)", "Live plant", "One site and day as an animated plant", "4.2"],
    ["(main)", "System designer", "Resize the plant and rerun every hour", "4.3"],
    ["(main)", "Compare sites", "The three sites side by side", "4.4"],
    ["Forecasting", "Forecast accuracy", "2025 day-ahead forecast errors", "4.5"],
    ["Forecasting", "Grid planning", "How forecasts change the grid-purchase plan", "4.6"],
    ["Forecasting", "Rolling test", "Each year forecast by a model trained on earlier years", "4.7"],
    ["Forecasting", "2026 forecast", "January to June 2026, computed against forecast", "4.8"],
    ["Reference", "Methodology", "Equations, parameters, sources and limits", "4.9"],
], [1.1, 1.4, 3.3, 0.7])
p("Your site, system design and chosen day carry over as you move between pages.")

h2("3.4  Common Controls")
h3("Site picker")
p(ix("site picker") + "Selects Laoag, Mactan or General Santos. Pages that show one site have it near the top.")
h3("Day picker")
p(ix("day picker") + "Pages that show a single day use the same day picker: the date with ‹ and › beside it.")
table([
    ["Control", "Action"],
    ["‹  ›", "Step back or forward one day. The Left and Right arrow keys do the same."],
    ["The date", "Opens a calendar. Use the month and year menus, or the arrows at the top, to change month, then click a day."],
    ["Type a date", 'Field at the bottom of the calendar. Accepts <font name="Mono">2025-03-14</font>, '
                    '<font name="Mono">14 Mar 2025</font>, <font name="Mono">Mar 14 2025</font>, '
                    '<font name="Mono">14/03/2025</font> (day first) or <font name="Mono">Mar 2025</font> '
                    "(first day of the month). Press Enter."],
    ["Shortcuts", "<i>Windiest</i>, <i>Sunniest</i>, <i>Calmest</i> (least energy) and <i>Random</i>, for the selected site."],
], [1.3, 5.2])
p("With the calendar open, the Left and Right arrow keys move one day, Up and Down move one week, Enter opens the "
  "highlighted day and Esc closes the calendar.")
p("Days range from 1 January 2020 to 30 June 2026. On Forecast accuracy and Grid planning the picker is limited to "
  "2025, the year those forecasts were tested on.")
h3("Charts")
p(ix("charts") + "Hover over a chart to read exact values. Drag across a chart to zoom in, and double-click to zoom back out. "
  "Click an item in a chart legend to hide or show that series.")

h2("3.5  Exiting the System")
p("Close the browser tab. Nothing needs to be saved. To stop a local copy, close the terminal window it opened, or "
  "press Ctrl+C in that window.")

# === 4 Using the System ================================================================================
h1("4  Using the System")
p("This section describes each page in menu order.")

h2("4.1  Map")
p(ix("Map page") + "The home page. A map of Luzon, the Visayas and Mindanao shows the three sites on one day, hour by hour.")
table([
    ["Control", "Location", "Action"],
    ["Key", "Top left", "Colors the regions by <i>Output</i> this hour, <i>Capacity factor</i> or <i>Wind share</i>."],
    ["Wind, Labels", "Top right", "Show or hide the moving wind particles and the site names. Particles follow each "
                                  "site's simulated hub-height wind."],
    ["Timeline", "Bottom", "Pick the day on the left, drag the yellow needle across the 24-hour chart, or select <b>PLAY</b>."],
    ["Regions and site tabs", "Map, right panel", "Hover a region to read its output, capacity factor and wind share. "
                                                  "Click a region or site tab to select it."],
], [1.4, 1.2, 3.9])
p("The right-hand panel has two tabs. <i>This day</i> shows the hour's output, the share of demand met by renewables, "
  "battery charge, energy flows against demand, and averages for January 2020 to June 2026. <i>2025 forecast test</i> "
  "shows how each forecasting method scored at the selected site.")
p("<b>To compare the three sites on one day</b>")
steps("Open <b>Map</b> and set the day in the timeline.",
      "Select <b>PLAY</b>, or drag the needle, and set the key to <i>Capacity factor</i>.",
      "Click each region and read its figures in the right-hand panel.")

h2("4.2  Live Plant")
p(ix("Live plant page") + "An animated plant for one site and day. The sky follows the hour, cloud cover follows the weather, the "
  "rotor speed follows wind output, and the dotted flows are scaled to MW.")
table([
    ["Result", "Meaning"],
    ["Generated", "Solar plus wind energy for the day, MWh."],
    ["Renewable share", "Share of the day's demand met by solar, wind or the battery."],
    ["Bought from grid", "Energy imported because generation and battery fell short, MWh."],
    ["Unused renewables", "Surplus that could not be used or stored, MWh."],
    ["Peak hub wind", "Highest wind speed at the 69 m hub that day, m/s."],
], [1.7, 4.8])
p("Below these figures, an hourly chart shows solar, wind, demand and battery charge.")
p("<b>To see how a typhoon-season day played out</b>")
steps("Open <b>Live plant</b> and choose a site.",
      "Open the calendar and pick a day between July and October, or use the <i>Calmest</i> shortcut.",
      "Watch the battery and the <i>From grid</i> flow as the day plays.")

h2("4.3  System Designer")
p(ix("System designer page") + "Resize the plant and rerun every hour from January 2020 to June 2026 for the selected site.")
table([
    ["Control", "Range", "Standard"],
    ["Solar capacity · MW", "0 to 3, steps of 0.25", "1.0"],
    ["Wind capacity · MW", "0 to 3, steps of 0.25", "1.0"],
    ["Battery · MWh", "0 to 8, steps of 0.5", "2.0"],
    ["Demand multiplier", "0.5 to 1.5, steps of 0.1", "1.0"],
    ["Other PV losses (under <b>Engineering assumptions</b>)", "0.05 to 0.25", "0.14"],
    ["PV temperature coefficient · /°C", "−0.0060 to −0.0020", "−0.0047"],
    ["Wind-shear exponent", "0.08 to 0.30", "0.14"],
    ["Wind net-output factor", "0.70 to 1.00", "0.90"],
], [3.0, 2.0, 1.5])
p("<b>Reset to standard design</b> returns every control to its standard value.")
p("Results show demand met by renewables, renewable energy, grid energy needed and unused renewables, each compared "
  "with the standard design. A yearly chart shows how demand was met. A month-by-hour chart, <i>Surplus by month and "
  "hour</i>, shows when the plant charges the battery (green) or draws on it (red).")
h3("Outage test")
p(ix("outage test") + "Simulates a grid outage. During the window, any shortfall becomes unmet demand.")
steps("Under <b>Outage test</b>, pick the day.",
      "Set <b>Starts at</b> (0:00 to 23:00) and <b>Lasts · hours</b> (1 to 24).",
      "Read <i>Demand served in outage</i>, <i>Unmet demand</i> and <i>First shortfall</i>. The chart shows the window "
      "with six hours either side.")
p("<b>To test a bigger battery</b>")
steps("Move <b>Battery · MWh</b> from 2 to 4.",
      "Read the change in <i>Demand met by renewables</i> and <i>Grid energy needed</i>.",
      "Run the outage test on an evening to see whether the extra storage carries the load.")
note("Note", "Your design carries over to Map and Live plant. Select <b>Reset to standard design</b> to return to the "
     "figures used elsewhere in this manual.")

h2("4.4  Compare Sites")
p(ix("Compare sites page") + "The three sites side by side for January 2020 to June 2026, with the same equipment at each: yearly "
  "energy by source, average output by month, wind roses (direction and speed at 69 m), and solar-wind "
  "complementarity. A complementarity value below zero means one source tends to fill in when the other is low.")

h2("4.5  Forecast Accuracy")
p(ix("Forecast accuracy page") + "Day-ahead forecasts issued at 00:00 for every day of 2025, a year held out from training. Three methods "
  "are compared: <i>XGBoost</i> (machine learning), <i>Previous day</i> (repeat yesterday) and <i>Past average</i> "
  "(the typical value for that month and hour).")
table([
    ["Part of the page", "What it shows"],
    ["Leaderboard", "Combined solar and wind error (MAE) for each method and site."],
    ["Source", "Switches the charts between <i>Combined</i>, <i>Solar</i> and <i>Wind</i>."],
    ["Error by hours ahead and by month", "Where each method does well or badly."],
    ["Single-day playback", "One 2025 day for one method. Turn off <b>Reveal the reference</b> to see the forecast "
                            "alone first. Turn on <b>Show all three methods</b> to overlay them."],
], [2.2, 4.3])
p("<b>To check a forecast on a specific day</b>")
steps("Open <b>Forecast accuracy</b> and pick a 2025 day under <i>Single-day playback</i>.",
      "Turn off <b>Reveal the reference</b>, play the day, then turn it back on to compare.",
      "Open <b>Grid planning</b> with the same day to see what that forecast did to the grid plan.")

h2("4.6  Grid Planning")
p(ix("Grid planning page", "adjustment") + "Each forecast sets an hourly grid-purchase plan at midnight. The real day is then replayed. "
  "<i>Adjustment</i> is the extra energy bought plus planned energy that was not needed. The page totals adjustment "
  "for 2025 by method. Under <i>Day replay</i>, pick a site, method and day to watch the plan (fixed at 00:00) "
  "against actual output.")

h2("4.7  Rolling Test")
p(ix("Rolling test page") + "The forecast rerun for 2024, 2025 and January to June 2026, each year predicted by a model that only saw "
  "earlier years.")
bullets("The fold grid shows which years were used to fit, select and test each model.",
        "<i>Every day, at midnight</i>: a calendar colors each day green where XGBoost beat the previous-day "
        "forecast and red where it lost. Use <b>Test</b> to choose the year. Click a day to open its 24-hour forecast.",
        "<i>Is the gap real?</i>: 95% intervals for the error difference from a seven-day block bootstrap "
        "(2,000 resamples). An interval left of zero favors XGBoost.",
        "<i>Shorter history?</i>: the same 2026 hours forecast with and without 2020 in training.")
p("A link at the top of the page opens 2026 forecast.")

h2("4.8  2026 Forecast")
p(ix("2026 forecast page", "computed output") + "Shows that the January to June 2026 forecasts came from models trained only on 2020 to 2025, and how "
  "they compare with the output computed from 2026 weather.")
table([
    ["Step", "Data", "Hours per site and source", "Purpose"],
    ["1  Fit", "2020–2024", "43,824", "Two candidate settings are trained."],
    ["2  Select", "2025", "8,760", "The better setting is kept."],
    ["3  Refit", "2020–2025", "52,584", "Retrained. The last hour is 31 Dec 2025, 23:00."],
    ["4  Forecast", "Jan–Jun 2026", "4,344", "Issued at 00:00 each day from the day before."],
    ["5  Score", "Jan–Jun 2026", "4,344", "Scored once against computed output."],
], [1.0, 1.2, 1.6, 2.7], keep=True)
bullets("<i>Computed vs forecast</i>: set <b>Show</b> to <i>Daily energy</i> for each 2026 day, or <i>Each hour</i> "
        "for all 4,344 hours against a perfect-forecast line plus one week in detail. A monthly table lists energy "
        "and error for all three methods.",
        "<i>Recompute it</i>: SolWind reruns its own equations on 2026 weather and compares every hour with the "
        "values the forecasts were scored against. The largest difference is under 0.000001 MW.",
        "<i>Download</i>: every 2026 hour at all three sites (Section 6.2).")
p("<b>To show that 2026 was forecast from earlier years only</b>")
steps("Open <b>Forecasting > 2026 forecast</b> and read the five steps.",
      "Set <b>Show</b> to <i>Each hour</i> to compare computed and forecast output.",
      "Read <i>Largest difference</i> under <i>Recompute it</i>.",
      "Select <b>Download 2026 computed vs forecast (CSV)</b> to keep the hourly evidence.")

h2("4.9  Methodology")
p(ix("Methodology page") + "Reference material in tabs: <i>Solar PV</i>, <i>Wind turbine</i>, <i>Battery</i> and <i>Forecasting</i>, "
  "each with its equations. Below the tabs are the fixed parameters, a comparison with related IEEE studies, the "
  "data sources and the limitations of the model.")

# === 5 Querying ========================================================================================
h1("5  Querying")
p(ix("querying") + "SolWind has no search box. You query it by choosing a page and setting its site, day, source and method. "
  "The table lists common questions and where to answer them.")
table([
    ["Question", "Page", "Settings"],
    ["How much did a site generate on a given day?", "Live plant", "Site, day"],
    ["Which site has the best capacity factor at a given hour?", "Map", "Day, key = <i>Capacity factor</i>, needle on the hour"],
    ["What was the windiest day at a site?", "Live plant or Map", "Day picker shortcut <i>Windiest</i>"],
    ["How much grid energy would a 4 MWh battery save?", "System designer", "Battery = 4, compare with standard"],
    ["Can the plant ride through an evening outage?", "System designer", "Outage test: day, start, length"],
    ["Which forecasting method is most accurate?", "Forecast accuracy", "Leaderboard, source"],
    ["In which months do forecasts miss most?", "Forecast accuracy", "Site, source, error by month"],
    ["How much does forecast error cost the grid plan?", "Grid planning", "Site, method"],
    ["Is XGBoost's advantage real?", "Rolling test", "<i>Is the gap real?</i>"],
    ["Was 2026 forecast without seeing 2026?", "2026 forecast", "Five steps, <i>Recompute it</i>"],
], [2.8, 1.4, 2.3])

# === 6 Reporting =======================================================================================
h1("6  Reporting")
p(ix("reporting", "CSV download") + "SolWind reports results on screen and as CSV files that open in any spreadsheet program. Times in "
  "every file are PHT.")
h2("6.1  Hourly Results for a Design")
steps("Open <b>System designer</b> and set the site and design.",
      "Open <b>Hourly results table and download</b> at the bottom of the page. The table shows the hours of the "
      "outage-test day.",
      "Select <b>Download every hour, 2020 to June 2026, for this design (CSV)</b>.")
p('The file is named <font name="Mono">solwind_&lt;site&gt;_2020_2026.csv</font> and has one row per hour (56,952 rows).')
table([
    ["Column", "Unit", "Meaning"],
    ["timestamp_pht", "—", "Start of the hour, PHT"],
    ["solar_mw", "MW", "Solar output"],
    ["wind_mw", "MW", "Wind output"],
    ["combined_mw", "MW", "Solar plus wind output"],
    ["demand_mw", "MW", "Demand, after the demand multiplier"],
    ["battery_soc_end_mwh", "MWh", "Battery charge at the end of the hour"],
    ["grid_import_mwh", "MWh", "Energy bought from the grid"],
    ["curtailed_renewable_mwh", "MWh", "Surplus that could not be used or stored"],
], [2.2, 0.8, 3.5])
h2("6.2  2026 Computed vs Forecast")
steps("Open <b>Forecasting > 2026 forecast</b>.",
      "Under <i>Download</i>, select <b>Download 2026 computed vs forecast (CSV)</b>.")
p('The file is named <font name="Mono">solwind_2026_computed_vs_forecast.csv</font> and holds every hour from '
  "1 January to 30 June 2026 at all three sites.")
table([
    ["Column", "Unit", "Meaning"],
    ["location", "—", "Site name"],
    ["target_timestamp_pht", "—", "The hour being forecast, PHT"],
    ["issued_at_pht", "—", "When the forecast was issued (00:00 of the same day)"],
    ["computed_mw", "MW", "Output computed from that hour's weather (the reference)"],
    ["xgboost_forecast_mw", "MW", "XGBoost forecast"],
    ["previous_day_forecast_mw", "MW", "Previous-day forecast"],
    ["training_climatology_forecast_mw", "MW", "Past-average forecast"],
], [2.6, 0.7, 3.2], keep=True)
# === 7 Messages and Troubleshooting ====================================================================
h1("7  Messages and Troubleshooting")
h2("7.1  On-Screen Messages")
table([
    ["Message or sign", "Meaning", "Action"],
    ["Wake-up screen (“This app has gone to sleep”)", "The hosted copy sleeps after a period without visitors.",
     "Select the button and wait about 30 seconds."],
    ["Running indicator in the top-right corner", "The page is calculating.", "Wait for it to finish."],
    ["Typed date turns red", "The date was not recognized or is outside 1 January 2020 to 30 June 2026.",
     'Use a listed format, for example <font name="Mono">14 Mar 2025</font>.'],
    ["Red error box on a page", "The page failed to load.", "Reload the page. If it remains, see Section 7.2."],
], [1.9, 2.3, 2.3])
h2("7.2  Problems and Fixes")
p(ix("troubleshooting") + "Find the problem in the left column and follow the fix.")
table([
    ["Problem", "Fix"],
    ["The first page takes a few seconds", "The equations run once over 170,856 site-hours and are then cached. Later pages are instant."],
    ["The map or calendar looks cut off", "Widen the browser window. Below 760 pixels the map switches to a stacked phone layout."],
    ["Arrow keys do nothing", "Click inside the map or day picker first so it has keyboard focus."],
    ["Numbers differ from those in this manual", "Your System designer settings carry across pages. Select <b>Reset to standard design</b>."],
    ["The local start file closes at once", "Check that Python 3.9 to 3.12 is installed and on the system path, then run the terminal commands in Section 3.2."],
    ["A page shows an error after an update", "On the hosted copy, reload the page. On a local copy, stop it and start it again."],
    ["A download does not start", "Allow downloads for the site in your browser settings, then select the button again."],
], [2.3, 4.2])
h2("7.3  Frequently Asked Questions")
p("<b>Is this real plant data?</b> No. Output is modeled from NASA POWER weather data for each site's grid cell. "
  "No plant was metered, and demand is one standard daily profile used at every site.")
p("<b>Why only next-day forecasts?</b> Grid purchases are scheduled the day before, and weather becomes much less "
  "predictable after a day or two.")
p("<b>Do I have to run forecasts myself?</b> No. Forecasts are stored for every day. The pickers only choose which day to inspect.")
p("<b>Why does the record stop at 30 June 2026?</b> NASA had not released complete solar data for later months when the data was collected.")
p("<b>Can SolWind forecast 2027?</b> No. A full-year outlook needs a separate long-term resource study, which SolWind does not provide.")
p("<b>What is outside the model?</b> Voltage, frequency, equipment failures, typhoon damage and costs. SolWind covers hourly energy only.")

# === Appendices ========================================================================================
h1("Appendix A  Glossary")
table([
    ["Term", "Meaning"],
    ["Adjustment", "Extra energy bought plus planned energy that was not needed, after the real day is known. Lower means the plan was closer to reality."],
    ["Battery charge (SOC)", "Energy stored, kept between 10% and 90% of capacity. Charging and discharging are each 95% efficient."],
    ["Capacity factor", "Average output divided by installed capacity. 20% means the plant produced a fifth of its maximum possible energy."],
    ["Computed output", "The modeled generation the forecasts are scored against, calculated from the actual weather of that hour. Also called the reference."],
    ["Day-ahead forecast", "A prediction of the next 24 hours, made at 00:00 using only information available then."],
    ["Demand met by renewables", "Share of demand served by solar, wind or the battery rather than the grid."],
    ["Fold", "One run of the rolling test: years to fit the model, a year to choose its settings, and a later period to test it."],
    ["Grid energy needed", "Energy bought from the grid when solar, wind and the battery fall short."],
    ["Hub-height wind", "Wind speed at the turbine's 69 m hub, estimated from NASA's 50 m wind."],
    ["MAE", "Mean absolute error: the average size of the forecast miss, in MW. Lower is better."],
    ["MW / MWh", "Power at an instant / energy over time. 1 MW for one hour is 1 MWh."],
    ["Past average", "A simple forecast using the typical output for that month and hour in the training years."],
    ["Previous day", "A simple forecast that repeats yesterday's hourly output."],
    ["Unused renewables", "Surplus that could not be used or stored because the battery was full."],
    ["XGBoost", "The machine-learning forecast: a gradient-boosted tree model that learns from the previous day's output and the calendar."],
], [1.8, 4.7])

h1("Appendix B  Standard Design Parameters")
p("These values are used whenever the standard design is selected. They can be read in full on the Methodology page.")
table([
    ["Parameter", "Value"],
    ["PV capacity (DC / AC limit)", "1.0 MW / 1.0 MW"],
    ["PV tilt and azimuth", "10°, facing south (180°)"],
    ["Ground albedo", "0.20"],
    ["PV temperature coefficient", "−0.0047 per °C, reference 25 °C"],
    ["Other PV losses", "14%"],
    ["Inverter efficiency", "96%"],
    ["Wind turbine", "EWT DW61, 1 MW, 69 m hub height"],
    ["Wind source height", "50 m (NASA POWER)"],
    ["Wind-shear exponent", "0.14"],
    ["Reference air density", "1.225 kg/m³"],
    ["Wind net-output factor", "0.90"],
    ["Battery", "2 MWh, 10% to 90% usable, 95% charge and 95% discharge efficiency"],
    ["Demand", "Standard daily profile: 0.25 MW overnight, rising to 0.65 MW in the evening"],
], [2.6, 3.9])

story.append(PageBreak())
p("Index", H1)
story.append(INDEX)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    Manual(str(OUT)).multiBuild(story, canvasmaker=INDEX.getCanvasMaker())
    print(OUT)
