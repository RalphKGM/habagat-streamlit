# Habagat

**Read tomorrow's sun and monsoon wind, then plan the grid around it.**

Habagat is the interactive product for our CSS142 research project. It simulates a 1 MW solar + 1 MW wind microgrid with a battery at three Philippine sites: Laoag (Luzon), Mactan (Visayas) and General Santos (Mindanao). The simulation runs on five years of hourly NASA POWER weather. Habagat then tests day-ahead forecasts (XGBoost vs. two baselines) on held-out years (2024, 2025 and January–June 2026) and shows what each forecast does to a grid-purchase plan.

> *Habagat* is the Filipino name for the southwest monsoon.

## What's inside

| Page | What it does |
|---|---|
| **Map** (home) | A night nautical chart of Luzon, Visayas and Mindanao, the three grid island groups our sites sit in, with depth-contour rings and lat/long ticks. Hover a region for a readout; click it or use the site switcher in the right-hand instrument rail. The timeline strip under the map plays or scrubs the day, the map recolors by output, capacity factor or wind share, and wind particles follow each site's simulated hub-height wind. The rail shows this hour's flows, the source split, five-year averages and the 2025 forecast test. |
| **Live plant** | Any day from 2020 to 2024 animated as a plant: sun position, rotor speed from wind output, cloud cover, battery charge and energy flows scaled to MW. Presets for the windiest, sunniest and hardest days. |
| **System designer** | Resize solar, wind, battery and demand, or adjust engineering assumptions, and rerun five years of physics. Includes a month × hour surplus heatmap and an outage test. |
| **Compare sites** | Energy mix, monthly profiles, wind roses and solar-wind complementarity. |
| **Forecast accuracy** | Model leaderboard, error by hours ahead and by month, and a single-day playback. |
| **Grid planning** | Total 2025 plan adjustment by method, plus an animated replay of the midnight plan against the actual day. |
| **Rolling test** | The forecast re-run for 2024, 2025 and Jan–Jun 2026, each year predicted by a model that only saw earlier years. A calendar of every forecast day (click one to open it), paired bootstrap intervals, grid-plan adjustment and the recent-window comparison. |
| **Methodology** | Equations, fixed assumptions, a comparison with related IEEE studies, sources and limitations. |

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
  mapview.py            two-way map component (Python side)
  scenes.py             data-driven animated scenes (iframe components)
  assets/map/           map component front end (plain HTML/JS, no build step)
  assets/ph_map.json    island-group outlines (Natural Earth, public domain)
  assets/               plant.html, replay.html, logo, icon
data/                   compact Parquet/CSV inputs (about 9.5 MB) + turbine-curve licence
scripts/build_data.py   rebuilds data/ from the full research project
scripts/build_rolling.py packages the team's rolling-year evaluation into data/rolling/
scripts/build_map.py    rebuilds ph_map.json from Natural Earth (needs shapely)
tests/                  parity + smoke tests
paper/                  IEEE paper (DOCX + PDF), current version
marketing/              30-second ad, ad kit, and AI ad-tool research
docs/DEPLOY.md          GitHub + Streamlit Community Cloud steps
docs/RELATED_WORK.md    comparison with the related IEEE studies
docs/DEFENSE_NOTES.md   pitch, demo path, numbers and deck corrections
```

## Data and honesty notes

- Weather: NASA POWER hourly v2.10 (gridded reanalysis, not on-site measurement).
- Generation is *reference modeled* output from that weather. It is not metered plant data.
- Demand is one standardized scenario used at every site. It is not measured NGCP or city load.
- Forecasts: the Forecast accuracy and Grid planning pages show the original experiment (trained 2020–2023, selected on 2024, scored once on 2025). The Rolling test page shows the chronological folds for 2024, 2025 and Jan–Jun 2026. July–September 2026 is not scored because NASA POWER had not released the solar inputs.
- Hourly energy balance only: no voltage, frequency, faults, degradation or repair times.
- Wind power curve: EWT DW61 1 MW from NLR turbine-models (BSD-3-Clause, licence in `data/`).
- Map outlines: Natural Earth (public domain).

## Credits

CSS142 project team. Built with Streamlit, Plotly, pandas and NumPy.
