# Habagat

**Read tomorrow's sun and monsoon wind, then plan the grid around it.**

Habagat is the interactive product for our CSS142 research project. It simulates a 1 MW solar + 1 MW wind microgrid with a battery at three Philippine sites: Laoag (Luzon), Mactan (Visayas) and General Santos (Mindanao). The simulation runs on five years of hourly NASA POWER weather. Habagat then tests day-ahead forecasts (XGBoost vs. two baselines) on a held-out 2025 and shows what each forecast does to a grid-purchase plan.

> *Habagat* is the Filipino name for the southwest monsoon.

## What's inside

| Page | What it does |
|---|---|
| **Overview** | Animated landing page, headline findings (computed live from the result files), the pipeline, and the three sites. |
| **Live plant** | Pick any day from 2020 to 2024 and watch it play out. The sun tracks the hour, the rotor speed follows simulated wind output, and clouds follow NASA POWER cloud cover. Energy particles flow in proportion to MW, and the battery fills and drains. One-click *Windiest / Sunniest / Hardest day* presets. |
| **System designer** | Resize solar, wind, battery and demand, or tweak engineering assumptions. Every change reruns the physics over 131,544 site-hours. KPIs show deltas against the paper's baseline. Also includes a month × hour *supply fingerprint* heatmap and an *outage drill*. |
| **Sites** | Map, energy mix, monthly profiles, wind roses, and solar-wind complementarity. |
| **Forecast lab** | Leaderboard, error by hours-ahead and by month, and an animated day playback with a hide-the-answer toggle. |
| **Grid planning** | Total 2025 plan adjustment per method, plus an animated replay: the midnight forecast is fixed while reality is revealed hour by hour. |
| **Methods** | Every equation, the fixed assumptions, sources and limitations. |

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Or double-click `Run Habagat.command` (macOS) or `Run Habagat.bat` (Windows). Python 3.9–3.12 works.

## Validation

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q
```

- `tests/test_engine.py` checks that the app's physics reproduces the paper's published tables. Five-year solar and wind energy match `site_summary.csv` to 1e-6 relative at all sites. Renewable demand coverage matches `demand_coverage_summary.csv` at 0, 2 and 4 MWh of battery.
- `tests/test_app.py` renders every page headlessly with Streamlit AppTest, using both the default design and a non-default one (no wind, 6 MWh battery, a different site), and fails on any exception.

## Project layout

```
streamlit_app.py        entry point: theme, navigation, shared state
app_pages/              one file per page
habagat/
  physics.py            solar + wind equations (verbatim from the research code)
  dispatch.py           demand scenario + battery dispatch (verbatim)
  data.py               cached loaders and the live simulation
  theme.py              palette, CSS, Plotly template, HTML helpers
  hero.py               animated landing hero (pure SVG + CSS)
  scenes.py             data-driven animated scenes (iframe components)
  assets/               plant.html, replay.html, logo, icon
data/                   compact Parquet/CSV inputs (5.4 MB) + turbine-curve licence
scripts/build_data.py   rebuilds data/ from the full research project
tests/                  parity + smoke tests
marketing/              30-second ad, ad kit, and AI ad-tool research
docs/DEPLOY.md          GitHub + Streamlit Community Cloud steps
```

## Data and honesty notes

- Weather: NASA POWER hourly v2.10 (gridded reanalysis, not on-site measurement).
- Generation is *reference modeled* output from that weather. It is not metered plant data.
- Demand is one standardized scenario used at every site. It is not measured NGCP or city load.
- Forecasts: trained 2020–2023, selected on 2024, scored once on 2025.
- Hourly energy balance only: no voltage, frequency, faults, degradation or repair times.
- Wind power curve: EWT DW61 1 MW from NLR turbine-models (BSD-3-Clause, licence in `data/`).

## Credits

CSS142 project team. Built with Streamlit, Plotly, pandas and NumPy.
