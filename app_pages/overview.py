import streamlit as st

from habagat import hero, theme
from habagat.data import (
    SITE_BLURB,
    SITE_ISLAND,
    SITE_SHORT,
    SITES,
    current_generation,
    headline_findings,
    load_weather,
    monthly_profile,
)

hero.render(
    kicker="CSS142 · Philippine renewable forecasting lab",
    title="Habagat",
    tagline="Read tomorrow’s sun and monsoon wind, then plan the grid around it.",
    sub="A solar-wind microgrid simulated at three Philippine sites from five years of NASA POWER weather. "
    "Machine-learning day-ahead forecasts are tested on a held-out 2025.",
)

c1, c2, c3, _ = st.columns([1, 1, 1, 1.4])
c1.page_link("app_pages/plant.py", label="Watch the live plant", icon=":material/play_circle:")
c2.page_link("app_pages/forecast.py", label="Open the forecast lab", icon=":material/insights:")
c3.page_link("app_pages/designer.py", label="Design your system", icon=":material/tune:")

found = headline_findings()
theme.stats(
    [
        (len(load_weather()), "", "hourly weather records simulated across Laoag, Mactan and General Santos, 2020–2024"),
        (found["test_hours"], "", "site-hours of 2025 held out from training and used only for the final test"),
        (round(found["mae_cut_max"]), "%", f"lower day-ahead error than the best simple baseline. "
         f"XGBoost wins at all three sites ({found['mae_cut_min']:.0f}–{found['mae_cut_max']:.0f}%)"),
        (round(found["plan_cut_max"]), "%", f"less grid-plan adjustment over the 2025 replay "
         f"({found['plan_cut_min']:.0f}–{found['plan_cut_max']:.0f}% across sites)"),
    ]
)

theme.header(
    "How it works",
    "From satellite weather to a <em>grid plan</em>",
    "Every number in Habagat traces back to one hourly pipeline. The physics is the same as in our paper. "
    "Change a setting anywhere and every page recomputes.",
)
theme.html(
    """<div class="hb-steps">
  <div class="hb-step"><div class="n">01</div><h5>Weather</h5><p>NASA POWER hourly irradiance, temperature, pressure and 50 m wind for three PAGASA stations.</p></div>
  <div class="hb-step"><div class="n">02</div><h5>Physics</h5><p>Sun position, tilted-panel irradiance and cell temperature for PV. Wind shear, air density and the EWT DW61 power curve for wind.</p></div>
  <div class="hb-step"><div class="n">03</div><h5>Forecast</h5><p>At midnight, XGBoost, the previous day and the past average each predict the next 24 hours.</p></div>
  <div class="hb-step"><div class="n">04</div><h5>Plan &amp; replay</h5><p>Each forecast sets a grid plan around a 2 MWh battery. Replaying the real day shows how much adjustment it needed.</p></div>
</div>"""
)

theme.header(
    "Three sites",
    "Same hardware, <em>three different skies</em>",
    "Identical 1 MW solar and 1 MW wind equipment, placed from the north to the south of the archipelago. "
    "The curves show the average combined output for each month.",
)
generation = current_generation()
cards = []
for site in SITES:
    frame = generation.loc[generation["location"] == site]
    years = frame["timestamp_pht"].dt.year.nunique()
    solar = frame["solar_mw"].sum() / years
    wind = frame["wind_mw"].sum() / years
    color = theme.SITE_COLOR[site]
    cards.append(
        f'<div class="hb-site" style="border-top:3px solid {color}">'
        f'<div class="tag">{SITE_ISLAND[site]}</div>'
        f"<h4>{SITE_SHORT[site]}</h4><p>{SITE_BLURB[site]}</p>"
        f'<div class="row"><div><b>{solar + wind:,.0f}</b>MWh / yr</div>'
        f'<div><b style="color:{theme.SUN_DEEP}">{100 * solar / (solar + wind):.0f}%</b>solar</div>'
        f'<div><b style="color:{theme.SEA}">{100 * wind / (solar + wind):.0f}%</b>wind</div></div>'
        f"{theme.sparkline(monthly_profile(frame).tolist(), color)}</div>"
    )
theme.html(f'<div class="hb-sites">{"".join(cards)}</div>')

theme.header("Honest by design", "What Habagat <em>is</em>, and what it isn’t")
theme.html(
    """<div class="hb-two">
  <div class="hb-card" style="border-top:3px solid var(--leaf)"><h5 style="color:var(--leaf)">It is</h5><ul>
    <li>A reproducible hourly energy simulation driven by NASA POWER reanalysis weather.</li>
    <li>A strict out-of-sample forecast test: trained 2020–2023, tuned 2024, scored once on 2025.</li>
    <li>A side-by-side comparison of grid plans made from each forecast, replayed against the same battery.</li>
  </ul></div>
  <div class="hb-card" style="border-top:3px solid var(--ember)"><h5 style="color:var(--ember)">It isn’t</h5><ul>
    <li>Metered plant data. Outputs are <i>reference modeled</i> from weather.</li>
    <li>Measured city demand. A standardized demand scenario is used at every site so they can be compared fairly.</li>
    <li>A grid-stability study. Voltage, frequency, faults and repairs are out of scope.</li>
  </ul></div>
</div>"""
)
