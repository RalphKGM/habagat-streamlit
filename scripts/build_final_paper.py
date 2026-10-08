"""Build the six-page ICMLANT 2026 paper from the IEEE template already used by the team's paper.

Usage: python scripts/build_final_paper.py TEMPLATE.docx FIG1.png OUT_DIR
Writes OUT_DIR/IEEE_Solar_Wind_Paper.docx (camera-ready, with authors) and
OUT_DIR/IEEE_Solar_Wind_Paper_anonymous.docx (double-blind submission).

The template supplies styles, section layout, equation and figure XML; all body text is written here.
Inline markup: **bold**, *italic*, _{subscript}, ^{superscript}.
"""
import re
import shutil
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

TEMPLATE, FIG1, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
APP_URL = "https://habagat.streamlit.app"

TITLE = "Day-Ahead Forecasting of Modeled Solar and Wind Generation and Battery Planning in Three Philippine Locations"
AUTHORS = [
    ("Ralph Kevin G. Morales", "rkgmorales@mymail.mapua.edu.ph"),
    ("Niccolo Ticzon", "nerticzon@mymail.mapua.edu.ph"),
    ("Jermaine Van Danganan", "jvadanganan@mymail.mapua.edu.ph"),
    ("David Solano", "dsolano@mymail.mapua.edu.ph"),
    ("David Ferrer", "dgcferrer@mymail.mapua.edu.ph"),
    ("Richard N. Monreal", "rmonreal@mapua.edu.ph"),
]
AFFILIATION = ["School of Information Technology", "Mapúa University", "Makati, Philippines"]

ABSTRACT = (
    "Hourly solar and wind output determines whether a hybrid plant can meet demand and how much grid energy must be "
    "scheduled a day ahead. This study models identical 1 MWdc photovoltaic and 1 MW wind systems at Laoag, Mactan and "
    "General Santos, representing Luzon, the Visayas and Mindanao, from NASA POWER hourly weather for January 2020 to "
    "June 2026. A common synthetic demand and battery rule measure demand coverage. Day-ahead forecasts issued at "
    "midnight are tested chronologically: 2024, 2025 and January–June 2026 are each predicted by models fitted and "
    "selected only on earlier years. XGBoost, random forest and ridge regression use the previous day’s output and "
    "calendar features and are compared with previous-day persistence and climatology. Laoag produced the most energy "
    "(3,563 MWh per year) and the highest demand coverage (65.4% without storage, 72.4% with 4 MWh). Both tree "
    "ensembles reduced combined mean absolute error by 17–30% against the better baseline at every site and test, and "
    "their mutual difference was not significant in seven of nine cases; ridge regression was not consistently better "
    "than the baselines. In a common 2 MWh battery replay, the ensembles reduced grid-plan adjustment by 15–25%. "
    "Generation is modeled and demand is synthetic, so the results describe modeled adequacy rather than measured "
    "plant performance."
)
KEYWORDS = ("solar photovoltaic, wind power, day-ahead forecasting, XGBoost, random forest, battery storage, "
            "Philippines")

REFERENCES = [
    "K. E. S. Pilario, J. A. Ibañez, X. N. Penisa, J. B. Obra, C. M. F. Odulio, and J. D. Ocon, “Spatio-temporal "
    "solar–wind complementarity assessment in the province of Kalinga-Apayao, Philippines using canonical correlation "
    "analysis,” *Sustainability*, vol. 14, no. 6, art. 3253, 2022, doi: 10.3390/su14063253.",
    "K. R. M. Supapo, L. Lozano, I. D. F. Tabañag, and E. M. Querikiol, “A backcasting analysis toward a 100% "
    "renewable energy transition by 2040 for off-grid islands,” *Energies*, vol. 15, no. 13, art. 4794, 2022, "
    "doi: 10.3390/en15134794.",
    "L. E. R. Luya, P. C. Gan, and M. A. A. Pedrasa, “Simulation platform for supply deficient microgrids,” in *Proc. "
    "2016 IEEE Innovative Smart Grid Technologies - Asia (ISGT-Asia)*, 2016, pp. 1171–1176, "
    "doi: 10.1109/ISGT-Asia.2016.7796551.",
    "C. S. Salvador and A. A. L. Manalo, “Planned renewable energy usage during power outage,” in *Proc. 25th Int. "
    "Conf. Systems Engineering*, 2017, pp. 377–385, doi: 10.1109/ICSEng.2017.79.",
    "A. G. Kavaz and A. Karazor, “Solar power forecasting by machine learning methods in a co-located wind and "
    "photovoltaic plant,” in *Proc. 12th Int. Conf. Power Science and Engineering*, 2023, pp. 55–59, "
    "doi: 10.1109/ICPSE59506.2023.10329287.",
    "S. Hu et al., “CNN-BiLSTM-Attention model for wind and solar power forecasting and analysis of factors affecting "
    "forecast accuracy,” in *Proc. 6th Int. Conf. Electrical, Electronic Information and Communication Engineering*, "
    "2025, pp. 347–350, doi: 10.1109/EEICE65049.2025.11033699.",
    "T. Chen and C. Guestrin, “XGBoost: A scalable tree boosting system,” in *Proc. 22nd ACM SIGKDD Int. Conf. "
    "Knowledge Discovery and Data Mining*, 2016, pp. 785–794, doi: 10.1145/2939672.2939785.",
    "L. Breiman, “Random forests,” *Machine Learning*, vol. 45, no. 1, pp. 5–32, 2001, "
    "doi: 10.1023/A:1010933404324.",
    "A. E. Hoerl and R. W. Kennard, “Ridge regression: Biased estimation for nonorthogonal problems,” "
    "*Technometrics*, vol. 12, no. 1, pp. 55–67, 1970, doi: 10.1080/00401706.1970.10488634.",
    "S. Freeman and E. Agar, “The impact of energy storage on the reliability of wind and solar power in New "
    "England,” *Heliyon*, vol. 10, no. 6, art. e27652, 2024, doi: 10.1016/j.heliyon.2024.e27652.",
    "E. Zarate-Perez, C. Santos-Mejía, and R. Sebastián, “Reliability of autonomous solar-wind microgrids with battery "
    "energy storage system applied in the residential sector,” *Energy Reports*, vol. 9, suppl. 9, pp. 172–183, 2023, "
    "doi: 10.1016/j.egyr.2023.05.239.",
    "NASA POWER, “Hourly API,” NASA Langley Research Center. [Online]. Available: "
    "https://power.larc.nasa.gov/docs/services/api/temporal/hourly/. Accessed: Oct. 5, 2026.",
    "PAGASA, “Climatological extremes: Laoag City, Ilocos Norte; Mactan International Airport, Cebu; and General "
    "Santos City, as of 2014.” [Online]. Available: https://pubfiles.pagasa.dost.gov.ph/cds/. Accessed: Oct. 5, 2026.",
    "EWT, “EWT DW61,” manufacturer brochure, n.d. [Online]. Available: "
    "https://ewtdirectwind.com/wp-content/uploads/2023/11/EWT_DW61.pdf. Accessed: Oct. 5, 2026.",
    "National Laboratory of the Rockies, “EWT DW61 1 MW turbine model,” archived theoretical power curve. [Online]. "
    "Available: https://github.com/NatLabRockies/turbine-models. Accessed: Oct. 5, 2026.",
    "NOAA Global Monitoring Division, “General solar position calculations.” [Online]. Available: "
    "https://gml.noaa.gov/grad/solcalc/solareqns.PDF. Accessed: Oct. 5, 2026.",
    "pvlib python, “pvlib.temperature.faiman,” version 0.9.0 documentation. [Online]. Available: "
    "https://pvlib-python.readthedocs.io/en/v0.9.0/generated/pvlib.temperature.faiman.html. Accessed: Oct. 5, 2026.",
    "A. P. Dobos, “PVWatts version 5 manual,” National Renewable Energy Laboratory, Rep. NREL/TP-6A20-62641, "
    "Sep. 2014.",
    "“The Plant-Level US multi-model WIND and generation (PLUSWIND) database: Metadata description,” U.S. Department "
    "of Energy Wind Data Hub, n.d. [Online]. Available: "
    "https://wdh.energy.gov/api/content/pluswind/documents/PLUSWIND-Documentation-20221213.pdf. Accessed: Oct. 5, 2026.",
    "scikit-learn developers, “Cross validation of time series data.” [Online]. Available: "
    "https://scikit-learn.org/stable/modules/cross_validation.html. Accessed: Oct. 5, 2026.",
]


# --- XML helpers -----------------------------------------------------------------------------------
def runs(text: str, size: int | None = None) -> str:
    """Inline markup to w:r elements."""
    out = []
    for tok in re.split(r"(\*\*.+?\*\*|\*[^*]+?\*|_\{[^}]+\}|\^\{[^}]+\})", text):
        if not tok:
            continue
        props = []
        if tok.startswith("**"):
            props.append("<w:b/>"); tok = tok[2:-2]
        elif tok.startswith("*"):
            props.append("<w:i/>"); tok = tok[1:-1]
        elif tok.startswith("_{"):
            props.append('<w:vertAlign w:val="subscript"/>'); tok = tok[2:-1]
        elif tok.startswith("^{"):
            props.append('<w:vertAlign w:val="superscript"/>'); tok = tok[2:-1]
        if size:
            props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
        rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
        out.append(f'<w:r>{rpr}<w:t xml:space="preserve">{escape(tok)}</w:t></w:r>')
    return "".join(out)


def para(style: str, text: str, ppr: str = "") -> str:
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{ppr}</w:pPr>{runs(text)}</w:p>'


def body(text: str) -> str:
    return para("BodyText", text)


def h1(text: str) -> str:
    return para("Heading1", text)


def h2(text: str) -> str:
    return para("Heading2", text)


SPACER = '<w:p><w:pPr><w:spacing w:after="60" w:line="20" w:lineRule="exact"/></w:pPr></w:p>'


def equation(math: str, number: int) -> str:
    """Linear math with X_{sub} subscripts, as an OMML paragraph numbered on the right."""
    def mrun(t, upright=False):
        sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if upright else ""
        return (f'<m:r>{sty}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/><w:sz w:val="20"/>'
                f'</w:rPr><m:t xml:space="preserve">{escape(t)}</m:t></m:r>')
    parts = []
    for tok in re.split(r"([A-Za-z]_\{[^}]+\})", math):
        if not tok:
            continue
        m = re.fullmatch(r"([A-Za-z])_\{([^}]+)\}", tok)
        if m:
            parts.append(f"<m:sSub><m:e>{mrun(m.group(1))}</m:e><m:sub>{mrun(m.group(2), True)}</m:sub></m:sSub>")
        else:
            for piece in re.split(r"([A-Za-z]+)", tok):
                if piece:
                    word = piece.isalpha() and len(piece) > 1
                    parts.append(mrun(piece, upright=word or not piece.isalpha()))
    return ('<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:ind w:firstLine="0"/><w:tabs><w:tab w:val="center" w:pos="2430"/>'
            '<w:tab w:val="right" w:pos="4860"/></w:tabs></w:pPr><w:r><w:tab/></w:r>'
            f'<m:oMath>{"".join(parts)}</m:oMath><w:r><w:tab/><w:t xml:space="preserve">({number})</w:t></w:r></w:p>')


BORDER = ('<w:tcBorders><w:top w:val="single" w:sz="4" w:color="000000"/><w:left w:val="single" w:sz="4" '
          'w:color="000000"/><w:bottom w:val="single" w:sz="4" w:color="000000"/><w:right w:val="single" w:sz="4" '
          'w:color="000000"/></w:tcBorders>')


def table(caption: str, header: list[str], rows: list[list[str]], widths: list[int], bold_min: bool = False) -> str:
    def cell(text, w, bold):
        b = "<w:b/>" if bold else '<w:b w:val="0"/>'
        return (f'<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="{w}"/>{BORDER}</w:tcPr><w:p><w:pPr><w:keepNext/>'
                '<w:spacing w:after="0" w:before="0" w:line="240" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr>'
                f'<w:r><w:rPr>{b}<w:sz w:val="15"/><w:szCs w:val="15"/></w:rPr><w:t xml:space="preserve">'
                f'{escape(text)}</w:t></w:r></w:p></w:tc>')

    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    xml = [f'<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="{sum(widths)}"/><w:jc w:val="center"/>'
           '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="50" w:type="dxa"/><w:right w:w="50" w:type="dxa"/>'
           f'</w:tblCellMar><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" '
           f'w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']
    xml.append('<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>'
               + "".join(cell(t, w, True) for t, w in zip(header, widths)) + "</w:tr>")
    for r in rows:
        best = None
        if bold_min:
            nums = [float(v) for v in r[1:]]
            best = 1 + nums.index(min(nums))
        xml.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>'
                   + "".join(cell(t, w, i == best) for i, (t, w) in enumerate(zip(r, widths))) + "</w:tr>")
    xml.append("</w:tbl>")
    return para("tablehead", caption, "<w:keepNext/>") + "".join(xml) + SPACER


def figure(template_xml: str, rid: str, cx_in: float, cy_in: float, pid: int) -> str:
    cx, cy = int(cx_in * 914400), int(cy_in * 914400)
    x = re.sub(r'r:embed="[^"]+"', f'r:embed="{rid}"', template_xml)
    x = re.sub(r'<wp:extent cx="\d+" cy="\d+"/>', f'<wp:extent cx="{cx}" cy="{cy}"/>', x)
    x = re.sub(r'<a:ext cx="\d+" cy="\d+"/>', f'<a:ext cx="{cx}" cy="{cy}"/>', x)
    x = re.sub(r'<wp:docPr id="\d+"', f'<wp:docPr id="{pid}"', x)
    return x


def caption(text: str) -> str:
    return para("figurecaption", text)


# --- content ---------------------------------------------------------------------------------------
MAE = [  # test, site, persistence, climatology, ridge, random forest, xgboost (combined MAE, MW)
    ("2024", "Laoag", "0.1428", "0.1681", "0.1303", "0.1075", "0.1088"),
    ("2024", "Mactan", "0.1002", "0.1257", "0.1054", "0.0811", "0.0826"),
    ("2024", "Gen. Santos", "0.0833", "0.0826", "0.0948", "0.0632", "0.0637"),
    ("2025", "Laoag", "0.1668", "0.1952", "0.1407", "0.1193", "0.1220"),
    ("2025", "Mactan", "0.1151", "0.1182", "0.1079", "0.0854", "0.0855"),
    ("2025", "Gen. Santos", "0.0783", "0.0725", "0.0870", "0.0588", "0.0600"),
    ("2026", "Laoag", "0.1346", "0.1608", "0.1317", "0.0948", "0.0953"),
    ("2026", "Mactan", "0.1140", "0.1232", "0.1126", "0.0854", "0.0837"),
    ("2026", "Gen. Santos", "0.0647", "0.0668", "0.0845", "0.0517", "0.0533"),
]
ADJ = [  # total grid-plan adjustment, MWh
    ("2024", "Laoag", "552.5", "724.5", "589.5", "448.7", "461.2"),
    ("2024", "Mactan", "525.4", "683.2", "537.7", "426.9", "434.6"),
    ("2024", "Gen. Santos", "553.7", "575.4", "623.2", "423.3", "424.9"),
    ("2025", "Laoag", "582.5", "696.1", "574.6", "449.6", "478.9"),
    ("2025", "Mactan", "665.9", "730.1", "635.8", "503.8", "507.7"),
    ("2025", "Gen. Santos", "602.5", "568.5", "664.9", "446.0", "457.7"),
    ("2026", "Laoag", "217.2", "316.4", "291.7", "174.3", "183.4"),
    ("2026", "Mactan", "293.6", "328.8", "282.4", "228.3", "219.5"),
    ("2026", "Gen. Santos", "240.3", "255.2", "307.3", "190.2", "196.7"),
]
METHOD_HEAD = ["Test / site", "Persist.", "Climat.", "Ridge", "RF", "XGBoost"]
METHOD_W = [1406, 692, 692, 692, 692, 692]


def content(anonymous: bool, fig) -> list[str]:
    app = ("An interactive web application that replays every modeled day, forecast and grid plan accompanies the "
           "paper (link withheld for double-blind review)." if anonymous else
           f"An interactive web application, SolWind, replays every modeled day, forecast and grid plan at {APP_URL}.")
    x = []
    x += [h1("Introduction"),
          body("Solar and wind output varies by hour, so annual energy alone cannot show whether generation coincides "
               "with demand or whether a battery can cover a shortfall. Day-ahead scheduling adds a second question: "
               "a grid purchase plan made at midnight is only as good as the forecast behind it. Philippine "
               "hybrid-system studies have examined resource complementarity, island transition scenarios and "
               "microgrid simulation [1]–[3], but few connect resource estimates, demand, storage and forecast-based "
               "plans under one set of assumptions."),
          body("This study places identical equipment at Laoag, Mactan and General Santos, which serve as case "
               "locations for Luzon, the Visayas and Mindanao; a single point cannot represent a whole island group. "
               "Generation is computed from NASA POWER weather with physical equations, so the work evaluates modeled "
               "hourly energy adequacy, not electrical stability or financial viability."),
          body("The contributions are a standardized three-site comparison, a chronological forecast test over two "
               "full years and one half year with five forecasting methods, and a battery replay that converts "
               f"forecast error into grid-plan adjustment. {app}")]

    x += [h1("Objectives"),
          body("The study compares modeled hourly solar and wind generation for identical equipment at three "
               "Philippine locations and tests whether a day-ahead forecast improves battery planning. Specifically, "
               "it aims to:"),
          body("**Objective 1.** Compare how identical 1 MWdc solar and 1 MW wind equipment would perform in Laoag, "
               "Mactan and General Santos."),
          body("**Objective 2.** Determine how much of the same synthetic demand each site could cover with different "
               "battery capacities."),
          body("**Objective 3.** Test whether learned day-ahead forecasts improve on simple baselines."),
          body("**Objective 4.** Assess whether better forecasts reduce a defined grid-planning error.")]

    x += [h1("Review of Related Literature"),
          body("Philippine studies have assessed solar–wind complementarity in Kalinga-Apayao [1], modeled a full "
               "renewable transition for off-grid islands with hourly utility load [2], and simulated hourly energy "
               "balances and interruptions in supply-deficient microgrids [3]. Salvador and Manalo simulated planned "
               "renewable use during a power outage [4]. These works size systems or study scenarios; none tests "
               "day-ahead forecasts against held-out years."),
          body("Kavaz and Karazor predicted the next 24 hours from the preceding 24 at a co-located wind and "
               "photovoltaic plant and found boosting methods competitive [5], while Hu et al. used a "
               "CNN-BiLSTM-attention network for wind and solar output [6]. Gradient-boosted trees [7] and random "
               "forests [8] suit tabular inputs such as lagged output and calendar terms, and ridge regression [9] is "
               "a regularized linear reference. Storage studies in New England [10] and in a residential microgrid "
               "[11] show that the value of a battery depends on hourly supply and demand, which motivates judging "
               "forecasts through a battery replay rather than error alone."),
          body("Most forecasting studies score one ratio split or one hold-out period from a single measured plant. "
               "This study instead tests whole years in chronological order at three sites with identical equipment, "
               "compares tree, linear and naive methods on the same hours, and links each forecast to the same "
               "storage plan, at the cost of using modeled rather than measured output.")]

    x += [h1("Methodology"),
          h2("Weather Data and Sites"),
          body("Hourly weather was downloaded from the NASA POWER Hourly API [12] for Laoag (18.18° N, 120.53° E), "
               "Mactan (10.32° N, 123.98° E) and General Santos (6.06° N, 125.10° E), using PAGASA station "
               "coordinates and elevations [13]. Values describe NASA grid cells, not station observations. Global, "
               "direct and diffuse irradiance, 2 m air temperature, 10 m and 50 m wind speed and surface pressure "
               "were converted from UTC to Philippine Standard Time (UTC+8). The archive runs from 1 January 2020 to "
               "30 June 2026, 56,952 hours per site; requests on 3 October 2026 returned complete irradiance only "
               "through June, so later days are excluded and nothing is interpolated. Checks found no duplicate "
               "keys, missing values, bound violations or energy-balance errors. Fig. 1 summarizes the workflow."),
          fig["pipeline"], caption("Study pipeline from archived weather to forecasts and the battery replay."),
          h2("Physical Generation Model"),
          body("Each site has a 1 MWdc fixed array tilted 10° toward the south and one 1 MW EWT DW61 turbine at a "
               "69 m hub [14], [15]. Solar position follows NOAA equations [16]. Plane-of-array irradiance G_{POA} "
               "sums direct, isotropic diffuse and ground-reflected light with albedo 0.20, and cell temperature "
               "follows the Faiman model [17]:"),
          equation("T_{cell} = T_{air} + G_{POA} / (25 + 6.84 V_{2})", 1),
          body("With g = G_{POA}/1000 and f_{T} = max[0, 1 − 0.0047(T_{cell} − 25)], AC output in MW is"),
          equation("P_{PV} = min[max(0.8256 g f_{T}, 0), 1]", 2),
          body("where 0.8256 combines 14% system losses and 96% inverter efficiency from PVWatts [18]. Wind speed is "
               "raised to hub height as V_{69} = V_{50}(69/50)^{0.14}, density-corrected as V_{69}(ρ/1.225)^{1/3} "
               "[19], and mapped through the turbine’s electrical power curve with a 0.90 net-output factor and a "
               "1 MW limit."),
          h2("Synthetic Demand and Battery"),
          body("All sites share one daily demand: 0.25 MW at 00:00–05:00, 0.40 MW at 06:00–08:00, 0.50 MW at "
               "09:00–16:00, 0.65 MW at 17:00–21:00 and 0.35 MW at 22:00–23:00. Each hour, generation serves demand "
               "first; surplus charges the battery and the remainder is curtailed, while a shortfall draws on the "
               "battery and then the grid. The battery has a 1 MW power limit, 95% charge and discharge efficiency "
               "and a 10–90% state-of-charge window, with stored energy E carried between hours:"),
          equation("E_{t+1} = E_{t} + 0.95 C_{t} − D_{t} / 0.95", 3),
          body("where C_{t} is charging and D_{t} is discharge to the load in hour t, in MWh. Capacities of 0, 1, 2 and 4 MWh were "
               "tested. Demand coverage is renewable-origin energy served divided by demand.")]

    x += [h2("Forecast Models and Chronological Tests"),
          body("Forecasts are issued at 00:00 for the next 24 hours. Each site and source (solar, wind) has its own "
               "model that predicts one target hour per row from 29 features: the previous day’s 24 hourly outputs, "
               "the horizon (1–24) and sine–cosine terms of day of year and hour. No future weather or output is "
               "used. XGBoost [7] has two predefined settings (350 trees of depth 5 or 500 of depth 3), random forest "
               "[8] uses 200 trees of depth 12 or unrestricted depth, and ridge regression [9] uses standardized "
               "inputs with a penalty of 1 or 100. Forecasts are bounded to 0–1 MW and summed into combined output. "
               "Persistence repeats the previous day’s output for the same hour, and climatology is the fitting-period "
               "mean for each month and hour."),
          table("Chronological evaluation periods", ["Test", "Fit", "Select", "Refit"],
                [["2024", "2020–2022", "2023", "2020–2023"], ["2025", "2020–2023", "2024", "2020–2024"],
                 ["2026 Jan–Jun", "2020–2024", "2025", "2020–2025"]], [1290, 1192, 1192, 1192]),
          body("Table I lists the expanding folds [20]. For each test, every model’s settings are chosen on the "
               "preceding year by mean absolute error (MAE), refitted through the year before the test, and scored "
               "once on the test year. The 2026 test holds 4,344 hours per site and source; its last training target "
               "is 31 December 2025, 23:00."),
          h2("Evaluation and Grid-Plan Replay"),
          body("MAE is computed in MW over all hours. Differences between two methods are summarized with a paired "
               "moving-block bootstrap of daily MAE differences (seven-day blocks, 2,000 resamples, 95% intervals). "
               "For planning, a reference run and every forecast share the 2 MWh battery and the same state of charge "
               "at midnight. Each forecast fixes the next day’s hourly grid purchases G_{plan} before the day is "
               "known, and grid-plan adjustment is the total of |G_{ref} − G_{plan}| over the test, that is, the "
               "extra energy bought plus planned energy that was not needed.")]

    x += [h1("Results and Discussion"),
          h2("Objective 1: Generation at Identical Sites"),
          fig["annual"], caption("Mean annual modeled energy, 2020–2024, from identical equipment."),
          body("Fig. 2 compares mean annual energy. Laoag produced the most combined output at 3,563 MWh per year, "
               "followed by Mactan at 2,751 MWh and General Santos at 1,866 MWh. Solar output was similar at all "
               "three sites, so wind explains most of Laoag’s advantage. Hourly solar–wind correlation was −0.139 at "
               "Laoag, −0.043 at Mactan and +0.097 at General Santos, so wind compensates for low solar output most "
               "at Laoag. June had the lowest mean output everywhere. One-factor changes to losses, wind shear, "
               "net-output factor and temperature coefficient moved combined energy by −5.0% to +3.3% without "
               "changing the site ranking."),
          h2("Objective 2: Demand Coverage and Storage"),
          fig["coverage"], caption("Renewable coverage of the common synthetic demand by battery capacity."),
          body("Fig. 3 shows that storage raised renewable demand coverage at every site: Laoag from 65.4% without a "
               "battery to 72.4% with 4 MWh, Mactan from 57.2% to 64.5% and General Santos from 42.4% to 46.8%. A "
               "battery only shifts energy between hours, so Fig. 4 tests fixed outages. In a 12-hour evening outage at Laoag on "
               "15 March 2022, "
               "unmet demand stayed at 2.069 MWh for every battery size because the battery began at its minimum "
               "charge, whereas a morning outage on the same date fell from 1.828 to 1.281 MWh. Nominal capacity "
               "therefore does not guarantee backup duration."),
          fig["outage"],
          caption("Laoag 12-hour hypothetical outages on 15 March 2022. The flat evening result reflects minimum "
                  "initial charge.")]

    x += [h2("Objective 3: Forecast Accuracy"),
          table("Combined output MAE by chronological test (MW)", METHOD_HEAD,
                [[f"{t}: {s}", *v] for t, s, *v in MAE], METHOD_W, bold_min=True),
          body("Table II reports combined MAE, with the lowest value in bold. XGBoost and random forest beat both "
               "baselines at every site in every test, reducing MAE by 17–29% and 19–30% against the better "
               "baseline. All 18 paired intervals for XGBoost against a baseline lie below zero; in 2026 at Laoag, "
               "for example, the difference from persistence is −0.039 MW (95% interval −0.057 to −0.024 MW). "
               "Between the two ensembles the interval includes zero in seven of nine cases and the largest gap is "
               "0.003 MW, so neither is clearly better. Ridge regression was worse than both ensembles everywhere and "
               "worse than the better baseline at General Santos in all three tests and at Mactan in 2024, because a linear model cannot "
               "follow the curved dependence of solar output on the hour."),
          fig["audit"],
          caption("January–June 2026 daily energy computed from 2026 weather and XGBoost forecasts issued at 00:00 by "
                  "models trained only on 2020–2025."),
          body("Fig. 5 compares the 2026 forecasts with output computed from 2026 weather; the forecasts follow the "
               "day-to-day swings, including windy spells, without having seen any 2026 data. Refitting on "
               "2021–2025 instead of 2020–2025 changed 2026 XGBoost MAE by only −0.0012 to +0.0007 MW, so dropping "
               "the oldest year has no consistent effect."),
          h2("Objective 4: Grid-Plan Adjustment"),
          table("Total grid-plan adjustment with a 2 MWh battery (MWh)", METHOD_HEAD,
                [[f"{t}: {s}", *v] for t, s, *v in ADJ], METHOD_W, bold_min=True),
          body("Lower forecast error carried through to the battery plan (Table III). Relative to the better "
               "baseline, XGBoost reduced total adjustment by 15–25% and random forest by 19–24%, and random forest "
               "needed the least adjustment in eight of nine cases. Ridge regression needed more adjustment than the "
               "better baseline in six cases. In January–June 2026, XGBoost plans needed 183.4, 219.5 and 196.7 MWh "
               "of adjustment at Laoag, Mactan and General Santos, against 217.2, 293.6 and 240.3 MWh for "
               "persistence. Because every method shares the reference battery state, the difference comes from the "
               "forecast alone; it measures planning disagreement, not cost.")]

    x += [h1("Conclusion and Future Work"),
          body("Identical equipment produced different modeled hourly outcomes at the three sites. Laoag led in "
               "energy and demand coverage, mainly through wind, and storage raised coverage everywhere without "
               "removing long low-output periods (Objectives 1 and 2). In chronological tests on 2024, 2025 and "
               "January–June 2026, XGBoost and random forest reduced day-ahead MAE by 17–30% against the better "
               "simple baseline at every site, were statistically indistinguishable from each other in most cases, "
               "and clearly outperformed ridge regression (Objective 3). These gains became 15–25% less grid-plan "
               "adjustment in a common battery replay (Objective 4)."),
          body("The targets are modeled from gridded weather and the demand is synthetic, so the results do not "
               "establish measured plant accuracy or savings. Future work will validate against measured weather, "
               "plant output and local load, complete the remaining 2026 months, and add numerical weather "
               "prediction inputs.")]

    x += [para("Heading5", "References")] + [para("references", r) for r in REFERENCES]
    return x


# --- assemble --------------------------------------------------------------------------------------
def elems(doc: str):
    b0 = doc.find("<w:body>") + 8
    b1 = doc.rfind("</w:body>")
    bodyxml, out, i = doc[b0:b1], [], 0
    pat = re.compile(r"<(w:p|w:tbl|w:sectPr)[ >]")
    while True:
        m = pat.search(bodyxml, i)
        if not m:
            break
        tag, depth = m.group(1), 0
        for mm in re.finditer(rf"<{tag}[ >]|</{tag}>|<{tag}/>", bodyxml[m.start():]):
            t = mm.group(0)
            depth += -1 if t.startswith("</") else (0 if t.endswith("/>") else 1)
            if depth == 0:
                j = m.start() + mm.end()
                break
        out.append(bodyxml[m.start():j])
        i = j
    return doc[:b0], out, doc[b1:]


def author_block(anonymous: bool, three_col_break: str) -> list[str]:
    ppr = ('<w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
           '<w:rPr><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>')
    if anonymous:
        one_col = three_col_break.replace('<w:cols w:num="3" w:space="720"/>', '<w:cols w:space="720"/>')
        return [para("Author", "Anonymous Authors", ppr),
                para("Author", "Affiliation and contact withheld for double-blind review", ppr), one_col]
    blocks = []
    for name, mail in AUTHORS:
        lines = [name, *AFFILIATION, mail]
        r = '<w:br/>'.join(f'<w:t xml:space="preserve">{escape(s)}</w:t>' for s in lines)
        sp = ppr.replace('w:after="0"', 'w:after="160"')
        blocks.append(f'<w:p><w:pPr><w:pStyle w:val="Author"/>{sp}</w:pPr><w:r><w:rPr><w:sz w:val="18"/></w:rPr>'
                      f'{r}</w:r></w:p>')
    return blocks + [three_col_break]


def build(anonymous: bool, dest: Path):
    work = OUT / ("_anon" if anonymous else "_named")
    shutil.rmtree(work, ignore_errors=True)
    with zipfile.ZipFile(TEMPLATE) as z:
        z.extractall(work)
    shutil.copy(FIG1, work / "word/media/image13.png")
    for stale in ["image17.png", "image18.png"]:
        (work / "word/media" / stale).unlink(missing_ok=True)
    rels = (work / "word/_rels/document.xml.rels").read_text()
    rels = re.sub(r'<Relationship Id="rId3[12]"[^>]*/>', "", rels)
    (work / "word/_rels/document.xml.rels").write_text(rels)

    doc = (work / "word/document.xml").read_text()
    head, els, tail = elems(doc)
    img_template = els[76]
    fig = {"pipeline": figure(img_template, "rId27", 3.36, 1.62, 101),
           "annual": figure(img_template, "rId28", 3.36, 1.68, 102),
           "coverage": figure(img_template, "rId29", 3.36, 1.68, 103),
           "outage": figure(img_template, "rId30", 3.36, 1.69, 105),
           "audit": figure(img_template, "rIdAudit2026", 3.36, 2.2, 104)}
    title = els[0].replace(re.search(r"<w:t>[^<]*</w:t>", els[0]).group(0), f"<w:t>{escape(TITLE)}</w:t>")
    front = [title, els[1], *author_block(anonymous, els[8]), els[9],
             para("Abstract", "Abstract—" + ABSTRACT, '<w:spacing w:before="0" w:after="200"/>'),
             para("Keywords", "Keywords—" + KEYWORDS)]
    new = front + content(anonymous, fig) + [els[-1]]
    (work / "word/document.xml").write_text(head + "".join(new) + tail)

    core = work / "docProps/core.xml"
    if core.exists():
        c = core.read_text()
        c = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator></dc:creator>" if anonymous else
                   "<dc:creator>R. K. G. Morales et al.</dc:creator>", c)
        c = re.sub(r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", "<cp:lastModifiedBy></cp:lastModifiedBy>", c)
        c = re.sub(r"<dc:title>.*?</dc:title>", f"<dc:title>{escape(TITLE)}</dc:title>", c)
        c = re.sub(r"<dc:subject>.*?</dc:subject>", "<dc:subject>ICMLANT 2026 submission</dc:subject>", c)
        c = re.sub(r"<dc:description>.*?</dc:description>", "<dc:description></dc:description>", c)
        core.write_text(c)

    dest.unlink(missing_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        names = sorted(p for p in work.rglob("*") if p.is_file())
        names.sort(key=lambda p: p.name != "[Content_Types].xml")
        for p in names:
            z.write(p, p.relative_to(work).as_posix())
    shutil.rmtree(work)
    print(dest)


build(False, OUT / "IEEE_Solar_Wind_Paper.docx")
build(True, OUT / "IEEE_Solar_Wind_Paper_anonymous.docx")
